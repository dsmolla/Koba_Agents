"""
Session management for Telegram bot users
"""

import json
import logging
import time
from typing import Optional, Dict
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from google_client.user_client import UserClient

from google_agent.agent import GoogleAgent
from google_agent.shared.llm_models import LLM_FLASH
from telegram_bot.config import Config
from telegram_bot.auth import AuthManager

logger = logging.getLogger(__name__)


class UserSession:
    """Represents a user's conversation session"""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.messages: list[BaseMessage] = []
        self.agent: Optional[GoogleAgent] = None
        self.last_activity = time.time()
        self.google_client: Optional[UserClient] = None

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = time.time()

    def is_expired(self) -> bool:
        """Check if session has expired"""
        return (time.time() - self.last_activity) > Config.SESSION_TIMEOUT

    def add_message(self, message: BaseMessage):
        """Add a message to the conversation history"""
        self.messages.append(message)
        self.update_activity()

    def clear_history(self):
        """Clear conversation history"""
        self.messages.clear()
        self.update_activity()

    def to_dict(self) -> dict:
        """Serialize session to dictionary"""
        return {
            "user_id": self.user_id,
            "messages": [self._message_to_dict(msg) for msg in self.messages],
            "last_activity": self.last_activity
        }

    @staticmethod
    def _message_to_dict(message: BaseMessage) -> dict:
        """Convert a message to dictionary"""
        return {
            "type": message.__class__.__name__,
            "content": message.content
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'UserSession':
        """Deserialize session from dictionary"""
        session = cls(data["user_id"])
        session.last_activity = data["last_activity"]

        for msg_data in data["messages"]:
            if msg_data["type"] == "HumanMessage":
                session.messages.append(HumanMessage(content=msg_data["content"]))
            elif msg_data["type"] == "AIMessage":
                session.messages.append(AIMessage(content=msg_data["content"]))

        return session


class SessionManager:
    """Manages user sessions for the Telegram bot"""

    def __init__(self):
        self.sessions: Dict[int, UserSession] = {}
        self.auth_manager = AuthManager()
        self.auth_flows: Dict[int, any] = {}  # Store auth flows temporarily

    def get_session(self, user_id: int) -> UserSession:
        """
        Get or create a user session

        Args:
            user_id: Telegram user ID

        Returns:
            UserSession object
        """
        # Check if session exists and is not expired
        if user_id in self.sessions:
            session = self.sessions[user_id]
            if session.is_expired():
                logger.info(f"Session expired for user {user_id}, creating new session")
                self._cleanup_session(user_id)
            else:
                session.update_activity()
                return session

        # Create new session
        session = UserSession(user_id)
        self.sessions[user_id] = session
        logger.info(f"Created new session for user {user_id}")

        # Try to load previous messages from disk
        self._load_session_from_disk(user_id)

        return session

    def get_or_create_agent(self, user_id: int) -> Optional[GoogleAgent]:
        """
        Get or create GoogleAgent for a user

        Args:
            user_id: Telegram user ID

        Returns:
            GoogleAgent instance or None if user not authenticated
        """
        session = self.get_session(user_id)

        # Return existing agent if available
        if session.agent is not None:
            return session.agent

        # Check if user is authenticated
        if not self.auth_manager.is_user_authenticated(user_id):
            logger.warning(f"User {user_id} not authenticated")
            return None

        try:
            # Create Google client using UserClient.from_file()
            # This automatically handles token validation and refresh
            token_path = Config.get_user_token_path(user_id)
            google_client = UserClient.from_file(
                token_path=str(token_path),
                credentials_path=Config.CREDS_PATH,
                scopes=Config.OAUTH_SCOPES
            )

            # Create agent
            agent = GoogleAgent(
                google_service=google_client,
                llm=LLM_FLASH,
                print_steps=Config.PRINT_STEPS
            )

            session.agent = agent
            session.google_client = google_client
            logger.info(f"Created GoogleAgent for user {user_id}")

            return agent

        except Exception as e:
            logger.error(f"Error creating agent for user {user_id}: {e}")
            return None

    def clear_session(self, user_id: int):
        """Clear a user's conversation history"""
        if user_id in self.sessions:
            self.sessions[user_id].clear_history()
            self._save_session_to_disk(user_id)
            logger.info(f"Cleared session for user {user_id}")

    def save_all_sessions(self):
        """Save all active sessions to disk"""
        for user_id in self.sessions:
            self._save_session_to_disk(user_id)
        logger.info("Saved all sessions to disk")

    def cleanup_expired_sessions(self):
        """Remove expired sessions from memory"""
        expired_users = [
            user_id for user_id, session in self.sessions.items()
            if session.is_expired()
        ]

        for user_id in expired_users:
            self._cleanup_session(user_id)

        if expired_users:
            logger.info(f"Cleaned up {len(expired_users)} expired sessions")

    def _cleanup_session(self, user_id: int):
        """Cleanup a specific session"""
        if user_id in self.sessions:
            self._save_session_to_disk(user_id)
            del self.sessions[user_id]
            logger.debug(f"Cleaned up session for user {user_id}")

    def _save_session_to_disk(self, user_id: int):
        """Save session to disk"""
        if user_id not in self.sessions:
            return

        session = self.sessions[user_id]
        session_path = Config.get_user_session_path(user_id)

        try:
            with open(session_path, 'w') as f:
                json.dump(session.to_dict(), f, indent=2)
            logger.debug(f"Saved session to disk for user {user_id}")
        except Exception as e:
            logger.error(f"Error saving session for user {user_id}: {e}")

    def _load_session_from_disk(self, user_id: int):
        """Load session from disk"""
        session_path = Config.get_user_session_path(user_id)

        if not session_path.exists():
            return

        try:
            with open(session_path, 'r') as f:
                data = json.load(f)
                loaded_session = UserSession.from_dict(data)

                # Only load if not expired
                if not loaded_session.is_expired():
                    self.sessions[user_id] = loaded_session
                    logger.info(f"Loaded session from disk for user {user_id}")
                else:
                    logger.info(f"Loaded session for user {user_id} was expired")

        except Exception as e:
            logger.error(f"Error loading session for user {user_id}: {e}")

    def store_auth_flow(self, user_id: int, flow):
        """Store authentication flow temporarily"""
        self.auth_flows[user_id] = flow

    def get_auth_flow(self, user_id: int):
        """Get stored authentication flow"""
        return self.auth_flows.get(user_id)

    def remove_auth_flow(self, user_id: int):
        """Remove authentication flow"""
        if user_id in self.auth_flows:
            del self.auth_flows[user_id]
