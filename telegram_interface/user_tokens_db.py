import asyncio
import logging
import aiosqlite
import sqlite3
import time
import os
from typing import Optional

from .config import Config
from .token_encryption import TokenEncryption
from uuid import uuid4

logger = logging.getLogger(__name__)


class UserTokensDB:
    def __init__(self):
        logger.info("Initializing UserTokensDB", extra={'db_path': str(Config.USER_TOKENS_DB)})
        self.db_path = Config.USER_TOKENS_DB
        self.encryptor = TokenEncryption()
        self._conn: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()
        logger.info("UserTokensDB initialized successfully")

    async def _get_connection(self) -> aiosqlite.Connection:
        """Get or create a persistent connection to the database."""
        if self._conn is None:
            self._conn = await aiosqlite.connect(self.db_path)
            logger.debug("Database connection established")
        return self._conn

    async def close(self):
        """Close the database connection."""
        if self._conn:
            await self._conn.close()
            self._conn = None
            logger.info("Database connection closed")

    async def _create_tables(self):
        """Create database tables if they don't exist. Call this once during initialization."""
        logger.debug("Creating database tables if not exists")
        async with self._lock:
            conn = await self._get_connection()
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
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS auth_flows (
                    state VARCHAR PRIMARY KEY,
                    telegram_id INTEGER,
                    pkce_verifier VARCHAR,
                    created_at REAL
                )
            ''')
            await conn.commit()
            
            # Set restrictive file permissions (User Read/Write only)
            try:
                os.chmod(self.db_path, 0o600)
                logger.debug("Set restrictive permissions on database file")
            except Exception as e:
                logger.warning(f"Could not set database file permissions: {e}")
                
        logger.debug("Database tables created/verified")

    async def add_user(self, telegram_id: int, oauth_token: dict):
        logger.info("Adding/updating user token", extra={'user_id': telegram_id})
        try:
            async with self._lock:
                conn = await self._get_connection()
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
            async with self._lock:
                conn = await self._get_connection()
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
            async with self._lock:
                conn = await self._get_connection()
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
            async with self._lock:
                conn = await self._get_connection()
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
            async with self._lock:
                conn = await self._get_connection()
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
            async with self._lock:
                conn = await self._get_connection()
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
            async with self._lock:
                conn = await self._get_connection()
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

    def add_user_sync(self, telegram_id: int, oauth_token: dict):
        """Sync: Add/Update user token (for Flask thread)."""
        import sqlite3
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    '''
                    INSERT INTO user_tokens (user_id, telegram_id, oauth_token)
                    VALUES (?, ?, ?)
                    ON CONFLICT(telegram_id)
                    DO UPDATE SET oauth_token = ?, updated_at = CURRENT_TIMESTAMP
                    ''',
                    (str(uuid4()), telegram_id, self.encryptor.encrypt(oauth_token), self.encryptor.encrypt(oauth_token))
                )
                conn.commit()
            logger.info("User token added/updated successfully (sync)", extra={'user_id': telegram_id})
        except Exception as e:
            logger.error("Failed to add/update user token (sync)", extra={
                'user_id': telegram_id,
                'error': str(e)
            }, exc_info=True)
            raise

    # --- Auth Flow Management (Async for Bot, Sync for Flask) ---

    async def add_auth_flow(self, state: str, telegram_id: int, pkce_verifier: Optional[str]):
        """Async: Store auth flow data."""
        try:
            async with self._lock:
                conn = await self._get_connection()
                await conn.execute(
                    'INSERT OR REPLACE INTO auth_flows (state, telegram_id, pkce_verifier, created_at) VALUES (?, ?, ?, ?)',
                    (state, telegram_id, pkce_verifier, time.time())
                )
                await conn.commit()
        except Exception as e:
            logger.error(f"Failed to add auth flow: {e}", exc_info=True)
            raise

    async def cleanup_expired_auth_flows(self, timeout_seconds: int) -> int:
        """Async: Remove expired auth flows."""
        expire_time = time.time() - timeout_seconds
        try:
            async with self._lock:
                conn = await self._get_connection()
                cursor = await conn.execute('DELETE FROM auth_flows WHERE created_at < ?', (expire_time,))
                await conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Failed to cleanup auth flows: {e}", exc_info=True)
            return 0

    def get_auth_flow_sync(self, state: str) -> tuple[int, Optional[str], float] | None:
        """Sync: Retrieve auth flow data (for Flask thread)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT telegram_id, pkce_verifier, created_at FROM auth_flows WHERE state = ?', (state,))
                row = cursor.fetchone()
                if row:
                    return row[0], row[1], float(row[2])
                return None
        except Exception as e:
            logger.error(f"Failed to get auth flow (sync): {e}", exc_info=True)
            return None

    def delete_auth_flow_sync(self, state: str):
        """Sync: Delete auth flow data (for Flask thread)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('DELETE FROM auth_flows WHERE state = ?', (state,))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to delete auth flow (sync): {e}", exc_info=True)

