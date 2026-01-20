from contextlib import asynccontextmanager

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from config import Config
from core.exceptions import ProviderNotConnectedError
from core.token_encryption import token_encryptor


class Database:
    def __init__(self):
        self._checkpointer = None
        self._pool = None

    async def connect(self):
        if self._pool is None:
            self._pool = AsyncConnectionPool(
                conninfo=Config.SUPABASE_DB_URL,
                max_size=30,
                min_size=1,
                open=False,
            )
            await self._pool.open()
            await self._pool.wait()

    async def disconnect(self):
        if self._pool:
            await self._pool.close()

    async def get_checkpointer(self):
        if self._checkpointer is None:
            await self.connect()
            self._checkpointer = AsyncPostgresSaver(self._pool)
            await self._checkpointer.setup()

        return self._checkpointer

    async def clear_thread(self, thread_id):
        checkpointer = await self.get_checkpointer()
        await checkpointer.adelete_thread(thread_id)

    async def get_provider_token(self, user_id: str, provider: str) -> dict:
        async with self._pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute("SELECT * FROM public.user_integrations WHERE user_id = %s AND provider = %s ",
                                  (user_id, provider))
                row = await cur.fetchone()
                if not row:
                    raise ProviderNotConnectedError(provider)

                return token_encryptor.decrypt(row['credentials'])

    async def set_provider_token(self, user_id: str, provider: str, token: dict):
        query = """
            INSERT INTO public.user_integrations (user_id, provider, credentials, updated_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (user_id, provider)
            DO UPDATE SET 
                credentials = EXCLUDED.credentials, updated_at = NOW()
        """
        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                encrypted_token = token_encryptor.encrypt(token)
                await cur.execute(query, (user_id, provider, encrypted_token))

    @asynccontextmanager
    async def connection(self):
        async with self._pool.connection() as conn:
            yield conn

    @asynccontextmanager
    async def transaction(self):
        async with self._pool.connection() as conn:
            async with conn.transaction():
                yield conn

    async def fetch_one(self, query: str, params: tuple = None):
        async with self._pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, params)
                return await cur.fetchone()

    async def fetch_all(self, query: str, params: tuple = None):
        async with self._pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, params)
                return await cur.fetchall()

    async def execute(self, query: str, params: tuple = None):
        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)


database = Database()