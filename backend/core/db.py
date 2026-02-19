import logging
from contextlib import asynccontextmanager

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from config import Config
from core.exceptions import ProviderNotConnectedError
from core.token_encryption import token_encryptor

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self._checkpointer = None
        self._pool = None

    async def connect(self):
        if self._pool is None:
            self._pool = AsyncConnectionPool(
                conninfo=Config.SUPABASE_DB_URL,
                max_size=10,
                min_size=1,
                open=False,
                check=AsyncConnectionPool.check_connection,
                kwargs={
                    "keepalives": 1,
                    "keepalives_idle": 30,
                    "keepalives_interval": 10,
                    "keepalives_count": 5,
                }
            )
            try:
                await self._pool.open()
                await self._pool.wait()
                logger.info("Database connection pool opened", extra={"max_size": 10})
            except Exception as e:
                logger.critical(f"Failed to open database connection pool: {e}", exc_info=True)
                raise

    async def disconnect(self):
        if self._pool:
            await self._pool.close()
            logger.info("Database connection pool closed")

    async def get_checkpointer(self):
        if self._checkpointer is None:
            await self.connect()
            self._checkpointer = AsyncPostgresSaver(self._pool)
            await self._checkpointer.setup()
            logger.info("LangGraph checkpointer ready")

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

    async def delete_provider_token(self, user_id: str, provider: str):
        query = "DELETE FROM public.user_integrations WHERE user_id = %s AND provider = %s"
        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (user_id, provider))

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

    async def get_user_timezone(self, user_id: str) -> str:
        row = await self.fetch_one(
            "SELECT timezone FROM public.user_settings WHERE user_id = %s",
            (user_id,)
        )
        return row['timezone'] if row else 'UTC'

    async def set_user_timezone(self, user_id: str, timezone: str):
        await self.execute(
            """
            INSERT INTO public.user_settings (user_id, timezone)
            VALUES (%s, %s)
            ON CONFLICT (user_id) DO UPDATE SET timezone = EXCLUDED.timezone, updated_at = NOW()
            """,
            (user_id, timezone)
        )

    async def pubsub_notification_exists(self, message_id: int) -> bool:
        row = await self.fetch_one("SELECT id FROM public.pubsub_notifications WHERE message_id = %s", (message_id,))
        return bool(row)


database = Database()