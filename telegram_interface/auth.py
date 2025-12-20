import asyncio
import logging
import time
from collections import defaultdict
from typing import Optional

import google.auth.exceptions

from google_client.auth import GoogleOAuthManager
from google_client.api_service import APIServiceLayer

from .token_encryption import TokenEncryption
from .user_tokens_db import UserTokensDB
from config import Config

logger = logging.getLogger(__name__)


class AuthManager:
    """Manages authentication and OAuth flows for users."""

    # Auth flow timeout in seconds (10 minutes)
    AUTH_FLOW_TIMEOUT = 600

    def __init__(self, redirect_uri: str) -> None:
        logger.info("Initializing AuthManager", extra={'redirect_uri': redirect_uri})
        self.auth_manager = GoogleOAuthManager(self._get_client_secret(), redirect_uri=redirect_uri)
        self._user_tokens_db = UserTokensDB()

        # Locks for thread safety
        self._token_refresh_locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)

        logger.info("AuthManager initialized successfully")

    @property
    def user_tokens_db(self) -> UserTokensDB:
        """Access to the user tokens database."""
        return self._user_tokens_db

    @staticmethod
    def _get_client_secret() -> dict:
        """Load Google OAuth client secrets from file."""
        return TokenEncryption().decrypt(Config.GOOGLE_OAUTH_CLIENT_TOKEN)

    async def is_user_authenticated(self, telegram_id: int) -> bool:
        """Check if user has a valid authentication token.

        Args:
            telegram_id: The Telegram user ID

        Returns:
            True if user is authenticated with a valid token, False otherwise
        """
        if user_token := await self._user_tokens_db.get_user_token(telegram_id):
            try:
                self.auth_manager.refresh_user_token(user_token)
                logger.debug("User authentication verified", extra={'user_id': telegram_id})
                return True
            except google.auth.exceptions.RefreshError as e:
                logger.warning("Token refresh failed during authentication check", extra={
                    'user_id': telegram_id,
                    'error': str(e)
                })
                return False
        logger.debug("No token found for user", extra={'user_id': telegram_id})
        return False

    async def create_api_service(self, telegram_id: int) -> Optional[APIServiceLayer]:
        """Create an authenticated API service layer for a user.

        Args:
            telegram_id: The Telegram user ID

        Returns:
            APIServiceLayer instance if successful, None if authentication fails
        """
        logger.debug("Attempting to create API service", extra={'user_id': telegram_id})
        if user_token := await self._user_tokens_db.get_user_token(telegram_id):
            timezone = await self._user_tokens_db.get_timezone(telegram_id) or 'UTC'
            logger.debug("Creating API service with timezone", extra={
                'user_id': telegram_id,
                'timezone': timezone
            })
            try:
                # Use lock for token refresh to prevent race conditions
                async with self._token_refresh_locks[telegram_id]:
                    google_service = APIServiceLayer(user_token, timezone)
                    await self._user_tokens_db.update_token(telegram_id, google_service.refresh_token())   # Will raise error if token invalid

                logger.info("API service created successfully", extra={
                    'user_id': telegram_id,
                    'timezone': timezone
                })
                return google_service
            except google.auth.exceptions.RefreshError as e:
                logger.error("Failed to create API service - token refresh error", extra={
                    'user_id': telegram_id,
                    'error': str(e)
                }, exc_info=True)
                await self._user_tokens_db.delete_token(telegram_id)
                return None

        logger.warning("Cannot create API service - no token found", extra={'user_id': telegram_id})
        return None

    async def get_user_timezone(self, telegram_id: int) -> Optional[str]:
        """Get the user's configured timezone.

        Args:
            telegram_id: The Telegram user ID

        Returns:
            Timezone string or None if not set
        """
        return await self._user_tokens_db.get_timezone(telegram_id)

    async def store_auth_flow(self, state: str, telegram_id: int, pkce_verifier: Optional[str] = None):
        """Store OAuth flow state in database.

        Args:
            state: OAuth state parameter
            telegram_id: The Telegram user ID
            pkce_verifier: Optional PKCE verifier for enhanced security
        """
        await self.cleanup_expired_auth_flows()

        logger.debug("Storing auth flow", extra={'user_id': telegram_id, 'has_pkce': pkce_verifier is not None})
        await self._user_tokens_db.add_auth_flow(state, telegram_id, pkce_verifier)

    def get_auth_flow(self, state: str) -> Optional[tuple[int, Optional[str]]]:
        """Get OAuth flow state from database (synchronous for Flask).

        Args:
            state: OAuth state parameter

        Returns:
            Tuple of (telegram_id, pkce_verifier) if found and not expired, None otherwise
        """
        result = self._user_tokens_db.get_auth_flow_sync(state)
        if result:
            telegram_id, pkce_verifier, timestamp = result
            # Check expiry
            if (time.time() - timestamp) > self.AUTH_FLOW_TIMEOUT:
                logger.warning("Auth flow expired", extra={
                    'user_id': telegram_id,
                    'age_seconds': time.time() - timestamp
                })
                self.remove_auth_flow(state)
                return None
            logger.debug("Auth flow retrieved", extra={'user_id': telegram_id})
            return telegram_id, pkce_verifier
        else:
            logger.warning("Auth flow not found")
        return None

    def remove_auth_flow(self, state: str):
        """Remove OAuth flow state from database (synchronous for Flask).

        Args:
            state: OAuth state parameter
        """
        self._user_tokens_db.delete_auth_flow_sync(state)

    async def cleanup_expired_auth_flows(self) -> int:
        """Clean up expired OAuth flow states from database.

        Returns:
            Number of expired flows cleaned up
        """
        count = await self._user_tokens_db.cleanup_expired_auth_flows(self.AUTH_FLOW_TIMEOUT)
        if count > 0:
            logger.info("Cleaned up expired auth flows", extra={'count': count})
        return count

    def generate_auth_url(self, scopes: list[str], state: str) -> str:
        """Generate OAuth authorization URL.

        Args:
            scopes: List of OAuth scopes to request
            state: OAuth state parameter for CSRF protection

        Returns:
            Authorization URL string
        """
        return self.auth_manager.generate_auth_url(scopes, state)

    def complete_auth_flow(self, code: str, scopes: list[str]) -> Optional[dict]:
        """Complete OAuth flow by exchanging code for token.

        Args:
            code: Authorization code from OAuth callback
            scopes: List of OAuth scopes

        Returns:
            Token dictionary if successful, None otherwise
        """
        try:
            return self.auth_manager.complete_auth_flow(code, scopes)
        except Exception as e:
            logger.error("Failed to complete auth flow", extra={'error': str(e)}, exc_info=True)
            return None

    async def update_timezone(self, telegram_id: int, timezone: str):
        """Update user's timezone preference.

        Args:
            telegram_id: The Telegram user ID
            timezone: Timezone string (e.g., 'America/New_York')
        """
        await self._user_tokens_db.update_timezone(telegram_id, timezone)
        logger.info("Timezone updated", extra={'user_id': telegram_id, 'timezone': timezone})

    async def delete_user_token(self, telegram_id: int):
        """Delete user's authentication token.

        Args:
            telegram_id: The Telegram user ID
        """
        await self._user_tokens_db.delete_token(telegram_id)
        logger.info("User token deleted", extra={'user_id': telegram_id})
