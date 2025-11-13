import logging
import aiosqlite

from .config import Config
from .token_encryption import TokenEncryption
from uuid import uuid4

logger = logging.getLogger(__name__)


class UserTokensDB:
    def __init__(self):
        logger.info("Initializing UserTokensDB", extra={'db_path': str(Config.USER_TOKENS_DB)})
        self.db_path = Config.USER_TOKENS_DB
        self.encryptor = TokenEncryption()
        logger.info("UserTokensDB initialized successfully")

    async def _create_tables(self):
        """Create database tables if they don't exist. Call this once during initialization."""
        logger.debug("Creating user_tokens table if not exists")
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
        logger.debug("Database tables created/verified")

    async def add_user(self, telegram_id: int, oauth_token: dict):
        logger.info("Adding/updating user token", extra={'user_id': telegram_id})
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
            logger.info("User token added/updated successfully", extra={'user_id': telegram_id})
        except Exception as e:
            logger.error("Failed to add/update user token", extra={
                'user_id': telegram_id,
                'error': str(e)
            }, exc_info=True)
            raise

    async def get_user_token(self, telegram_id: int) -> dict | None:
        logger.debug("Retrieving user token", extra={'user_id': telegram_id})
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                async with conn.execute(
                    'SELECT oauth_token FROM user_tokens WHERE telegram_id = ?',
                    (telegram_id,)
                ) as cursor:
                    result = await cursor.fetchone()
                    if result and result[0]:
                        logger.debug("User token found", extra={'user_id': telegram_id})
                        return self.encryptor.decrypt(result[0])
                    logger.debug("No token found for user", extra={'user_id': telegram_id})
                    return None
        except Exception as e:
            logger.error("Failed to retrieve user token", extra={
                'user_id': telegram_id,
                'error': str(e)
            }, exc_info=True)
            return None

    async def update_token(self, telegram_id: int, oauth_token: dict):
        logger.info("Updating user token", extra={'user_id': telegram_id})
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute('''
                    UPDATE user_tokens
                    SET oauth_token = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE telegram_id = ?
                ''', (self.encryptor.encrypt(oauth_token), telegram_id))
                await conn.commit()
            logger.info("User token updated successfully", extra={'user_id': telegram_id})
        except Exception as e:
            logger.error("Failed to update user token", extra={
                'user_id': telegram_id,
                'error': str(e)
            }, exc_info=True)
            raise

    async def delete_token(self, telegram_id: int):
        logger.info("Deleting user token", extra={'user_id': telegram_id})
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
            logger.info("User token deleted successfully", extra={'user_id': telegram_id})
        except Exception as e:
            logger.error("Failed to delete user token", extra={
                'user_id': telegram_id,
                'error': str(e)
            }, exc_info=True)
            raise

    async def delete_user(self, telegram_id: int):
        logger.warning("Deleting user completely", extra={'user_id': telegram_id})
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute(
                    'DELETE FROM user_tokens WHERE telegram_id = ?',
                    (telegram_id,)
                )
                await conn.commit()
            logger.warning("User deleted from database", extra={'user_id': telegram_id})
        except Exception as e:
            logger.error("Failed to delete user", extra={
                'user_id': telegram_id,
                'error': str(e)
            }, exc_info=True)
            raise

    async def update_timezone(self, telegram_id: int, timezone: str):
        logger.info("Updating user timezone", extra={'user_id': telegram_id, 'timezone': timezone})
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
            logger.info("User timezone updated successfully", extra={
                'user_id': telegram_id,
                'timezone': timezone
            })
        except Exception as e:
            logger.error("Failed to update timezone", extra={
                'user_id': telegram_id,
                'timezone': timezone,
                'error': str(e)
            }, exc_info=True)
            raise

    async def get_timezone(self, telegram_id: int) -> str | None:
        logger.debug("Retrieving user timezone", extra={'user_id': telegram_id})
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                async with conn.execute(
                    'SELECT timezone FROM user_tokens WHERE telegram_id = ?',
                    (telegram_id,)
                ) as cursor:
                    result = await cursor.fetchone()
                    if result and result[0]:
                        logger.debug("Timezone found", extra={'user_id': telegram_id, 'timezone': result[0]})
                        return result[0]
                    logger.debug("No timezone set for user", extra={'user_id': telegram_id})
                    return None
        except Exception as e:
            logger.error("Failed to retrieve timezone", extra={
                'user_id': telegram_id,
                'error': str(e)
            }, exc_info=True)
            return None
