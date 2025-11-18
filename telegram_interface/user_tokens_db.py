import aiosqlite

from .config import Config
from .token_encryption import TokenEncryption
from uuid import uuid4


class UserTokensDB:
    def __init__(self):
        self.db_path = Config.USER_TOKENS_DB
        self.encryptor = TokenEncryption()

    async def _create_tables(self):
        """Create database tables if they don't exist. Call this once during initialization."""
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS user_tokens (
                    user_id VARCHAR PRIMARY KEY,
                    telegram_id INTEGER UNIQUE,
                    timezone VARCHAR,
                    oauth_token VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await conn.commit()

    async def add_user(self, telegram_id: int, oauth_token: dict):
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute(
                    '''
                    INSERT INTO user_tokens (user_id, telegram_id, oauth_token)
                    VALUES (?, ?, ?)
                    ON CONFLICT(telegram_id)
                    DO UPDATE SET oauth_token = ?, updated_at = CURRENT_TIMESTAMP
                    ''',
                    (str(uuid4()), telegram_id, self.encryptor.encrypt(oauth_token), self.encryptor.encrypt(oauth_token))
                )
                await conn.commit()
        except Exception:
            raise

    async def get_user_token(self, telegram_id: int) -> dict | None:
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                async with conn.execute(
                    'SELECT oauth_token FROM user_tokens WHERE telegram_id = ?',
                    (telegram_id,)
                ) as cursor:
                    result = await cursor.fetchone()
                    if result and result[0]:
                        return self.encryptor.decrypt(result[0])
                    return None
        except Exception:
            return None

    async def update_token(self, telegram_id: int, oauth_token: dict):
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute('''
                    UPDATE user_tokens
                    SET oauth_token = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE telegram_id = ?
                ''', (self.encryptor.encrypt(oauth_token), telegram_id))
                await conn.commit()
        except Exception:
            raise

    async def delete_token(self, telegram_id: int):
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute(
                    '''
                    UPDATE user_tokens
                    SET oauth_token = NULL, updated_at = CURRENT_TIMESTAMP
                    WHERE telegram_id = ?
                    ''',
                    (telegram_id,)
                )
                await conn.commit()
        except Exception:
            raise

    async def delete_user(self, telegram_id: int):
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute(
                    'DELETE FROM user_tokens WHERE telegram_id = ?',
                    (telegram_id,)
                )
                await conn.commit()
        except Exception:
            raise

    async def update_timezone(self, telegram_id: int, timezone: str):
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute(
                    '''
                    UPDATE user_tokens
                    SET timezone = ?
                    WHERE telegram_id = ?
                    ''',
                    (timezone, telegram_id)
                )
                await conn.commit()
        except Exception:
            raise

    async def get_timezone(self, telegram_id: int) -> str | None:
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                async with conn.execute(
                    'SELECT timezone FROM user_tokens WHERE telegram_id = ?',
                    (telegram_id,)
                ) as cursor:
                    result = await cursor.fetchone()
                    if result and result[0]:
                        return result[0]
                    return None
        except Exception:
            return None
