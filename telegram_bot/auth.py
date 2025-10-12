"""
Google OAuth authentication flow for Telegram bot users
Using google-api-client-wrapper for consistency with the main agent
"""

import json
import logging

from google_auth_oauthlib.flow import InstalledAppFlow

from telegram_bot.config import Config

logger = logging.getLogger(__name__)


class AuthManager:
    """Manages Google OAuth authentication for Telegram users"""

    def __init__(self):
        self.creds_path = Config.CREDS_PATH
        self.scopes = Config.OAUTH_SCOPES

    def is_user_authenticated(self, user_id: int) -> bool:
        """
        Check if a user has valid credentials

        Args:
            user_id: Telegram user ID

        Returns:
            True if user has a valid token file, False otherwise
        """
        token_path = Config.get_user_token_path(user_id)

        if not token_path.exists():
            return False

        try:
            # Try to load the token file to verify it's valid JSON
            with open(token_path, 'r') as f:
                token_data = json.load(f)
                # Basic validation - check required fields exist
                required_fields = ['token', 'refresh_token', 'token_uri', 'client_id']
                return all(field in token_data for field in required_fields)
        except Exception as e:
            logger.error(f"Error validating token for user {user_id}: {e}")
            return False

    def generate_auth_url(self) -> tuple[str, InstalledAppFlow]:
        """
        Generate OAuth URL for user authentication

        Returns:
            Tuple of (auth_url, flow) where flow is needed to complete authentication
        """
        logger.info(f"Creating OAuth flow with redirect_uri: {Config.OAUTH_REDIRECT_URI}")

        flow = InstalledAppFlow.from_client_secrets_file(
            self.creds_path,
            scopes=self.scopes,
            redirect_uri=Config.OAUTH_REDIRECT_URI
        )

        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )

        logger.info(f"Generated auth URL: {auth_url[:100]}...")
        return auth_url, flow

    def complete_authentication(
        self,
        user_id: int,
        auth_code: str,
        flow: InstalledAppFlow
    ) -> bool:
        """
        Complete OAuth flow with authorization code

        Args:
            user_id: Telegram user ID
            auth_code: Authorization code from user
            flow: The flow object from generate_auth_url

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            logger.info(f"Attempting to fetch token with code for user {user_id}")
            logger.debug(f"Auth code (first 20 chars): {auth_code[:20]}...")

            flow.fetch_token(code=auth_code)
            creds = flow.credentials

            if creds and creds.valid:
                # Save credentials in JSON format (compatible with UserClient.from_file)
                # The to_json() method returns a JSON string with all required fields
                token_path = Config.get_user_token_path(user_id)
                with open(token_path, 'w') as token_file:
                    token_file.write(creds.to_json())
                logger.info(f"Successfully authenticated user {user_id}")
                return True
            else:
                logger.error(f"Invalid credentials received for user {user_id}")
                return False

        except Exception as e:
            logger.error(f"Authentication failed for user {user_id}: {e}", exc_info=True)
            return False

    def revoke_authentication(self, user_id: int) -> bool:
        """
        Revoke user's credentials and delete token file

        Args:
            user_id: Telegram user ID

        Returns:
            True if successful, False otherwise
        """
        try:
            token_path = Config.get_user_token_path(user_id)

            if token_path.exists():
                token_path.unlink()
                logger.info(f"Revoked credentials for user {user_id}")
                return True
            else:
                logger.warning(f"No credentials found for user {user_id}")
                return False

        except Exception as e:
            logger.error(f"Error revoking credentials for user {user_id}: {e}")
            return False
