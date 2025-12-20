"""
Shared AuthManager instance for the application.

This module provides a singleton AuthManager instance that is shared
across all components (bot, session_manager, oauth_callback) to ensure
consistent authentication state and avoid resource conflicts.
"""
import logging

from .auth import AuthManager
from config import Config

logger = logging.getLogger(__name__)

# Single shared instance used by all components
auth_manager = AuthManager(redirect_uri=Config.OAUTH_REDIRECT_URI)

logger.info("Shared AuthManager instance created", extra={
    'redirect_uri': Config.OAUTH_REDIRECT_URI
})
