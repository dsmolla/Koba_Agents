import os
from contextlib import asynccontextmanager

from core.exceptions import ProviderNotConnectedError
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import AsyncConnectionPool


class Database:
    def __init__(self):
        self._checkpointer = None
        self._pool = None
        self._supabase = None

    async def connect(self):
        if self._pool is None:
            self._pool = AsyncConnectionPool(
                conninfo=os.environ.get("SUPABASE_DB_URL"),
                max_size=30,
                min_size=2,
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

    async def get_provider_token(self, user_id, provider) -> dict:
        async with self._pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute("SELECT * FROM public.user_integrations WHERE user_id = %s AND provider = %s ",
                                  (user_id, provider))
                row = await cur.fetchone()
                if not row:
                    raise ProviderNotConnectedError(provider)
                return row['credentials']

    async def insert_provider_token(self, user_id, provider, token):
        query = """
            INSERT INTO public.user_integrations (user_id, provider, credentials, updated_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (user_id, provider)
            DO UPDATE SET 
                credentials = EXCLUDED.credentials, updated_at = NOW()
        """
        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (user_id, provider, Jsonb(token)))

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


db = Database()
