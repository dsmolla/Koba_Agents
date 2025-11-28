import json
import logging
import time
from typing import Optional

import aiofiles
import google.auth.exceptions

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.globals import set_debug

from google_agent.agent import GoogleAgent
from google_agent.shared.llm_models import LLM_FLASH
from google_client.auth import GoogleOAuthManager
from google_client.api_service import APIServiceLayer

from .user_tokens_db import UserTokensDB
from .config import Config

logger = logging.getLogger(__name__)


class UserSession:
    def __init__(self, telegram_id: int):
        self.telegram_id = telegram_id
        self.messages: list[BaseMessage] = []
        self.agent: Optional[GoogleAgent] = None
        self.last_activity: float = time.time()

    def update_activity(self):
        self.last_activity = time.time()

    def is_expired(self) -> bool:
        return (time.time() - self.last_activity) > Config.SESSION_TIMEOUT

    def add_message(self, message: BaseMessage):
        self.messages.append(message)
        self.update_activity()

    def clear_history(self):
        self.messages.clear()
        self.update_activity()

    def to_dict(self) -> dict:
        return {
            'telegram_id': self.telegram_id,
            'messages': self._convert_messages_to_dict(),
            'last_activity': self.last_activity
        }

    def _convert_messages_to_dict(self) -> list[dict]:
        return [{
            'type': message.__class__.__name__,
            'content': message.content
        } for message in self.messages]

    @classmethod
    def from_dict(cls, data: dict) -> 'UserSession':
        session = cls(data['telegram_id'])
        session.last_activity = time.time()

        for msg_data in data['messages']:
            if msg_data['type'] == 'HumanMessage':
                session.messages.append(HumanMessage(content=msg_data['content']))
            elif msg_data['type'] == 'AIMessage':
                session.messages.append(AIMessage(content=msg_data['content']))
            elif msg_data['type'] == 'ToolMessage':
                session.messages.append(ToolMessage(content=msg_data['content']))

        return session


class SessionManager:
    # Auth flow timeout in seconds (10 minutes)
    AUTH_FLOW_TIMEOUT = 600

    def __init__(self, redirect_uri: str) -> None:
        logger.info("Initializing SessionManager", extra={'redirect_uri': redirect_uri})
        self.sessions: dict[int, UserSession] = {}
        self.auth_manager = GoogleOAuthManager(self._get_client_secret(), redirect_uri=redirect_uri)
        self.user_tokens_db = UserTokensDB()
        # Store (telegram_id, timestamp) tuples to enable cleanup
        self.auth_flows: dict[str, tuple[int, float]] = {}

        set_debug(Config.LANGGRAPH_DEBUG)
        logger.info("SessionManager initialized successfully", extra={
            'langgraph_debug_mode': Config.LANGGRAPH_DEBUG,
            'session_timeout': Config.SESSION_TIMEOUT
        })

    @staticmethod
    def _get_client_secret() -> dict:
        with open(Config.CLIENT_CREDS_PATH, 'r') as f:
            return json.load(f)

    async def is_user_authenticated(self, telegram_id: int) -> bool:
        if user_token := await self.user_tokens_db.get_user_token(telegram_id):
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

    async def get_session(self, telegram_id: int) -> UserSession:
        if telegram_id in self.sessions:
            session = self.sessions[telegram_id]
            if session.is_expired():
                logger.info("Session expired, cleaning up", extra={'user_id': telegram_id})
                self._cleanup_session(telegram_id)
            else:
                logger.debug("Existing session retrieved", extra={
                    'user_id': telegram_id,
                    'message_count': len(session.messages)
                })
                session.update_activity()
                return session

        logger.info("Creating new session", extra={'user_id': telegram_id})
        session = UserSession(telegram_id)
        session.agent = await self.create_agent(telegram_id)
        self.sessions[telegram_id] = session
        logger.info("New session created", extra={
            'user_id': telegram_id,
            'has_agent': session.agent is not None
        })
        return session

    async def create_agent(self, telegram_id: int) -> Optional[GoogleAgent]:
        logger.debug("Attempting to create agent", extra={'user_id': telegram_id})
        if user_token := await self.user_tokens_db.get_user_token(telegram_id):
            timezone = await self.user_tokens_db.get_timezone(telegram_id) or 'UTC'
            logger.debug("Creating agent with timezone", extra={
                'user_id': telegram_id,
                'timezone': timezone
            })
            try:
                google_service = APIServiceLayer(user_token, timezone)
                await self.user_tokens_db.update_token(telegram_id, google_service.refresh_token())   # Will raise error if token invalid
                logger.info("GoogleAgent created successfully", extra={
                    'user_id': telegram_id,
                    'timezone': timezone
                })
                return GoogleAgent(
                    google_service=google_service,
                    llm=LLM_FLASH,
                    config={
                        "configurable":
                            {"thread_id": telegram_id}
                    }
                )
            except google.auth.exceptions.RefreshError as e:
                logger.error("Failed to create agent - token refresh error", extra={
                    'user_id': telegram_id,
                    'error': str(e)
                }, exc_info=True)
                await self.user_tokens_db.delete_token(telegram_id)
                return None

        logger.warning("Cannot create agent - no token found", extra={'user_id': telegram_id})
        return None

    async def save_session_to_disk(self, telegram_id: int) -> bool:
        session = self.sessions.get(telegram_id)
        if session is None:
            logger.debug("Cannot save session - session not found", extra={'user_id': telegram_id})
            return False

        if session.is_expired():
            logger.debug("Cannot save session - session expired", extra={'user_id': telegram_id})
            return False

        session_path = Config.get_user_session_path(telegram_id)
        try:
            async with aiofiles.open(session_path, 'w') as f:
                await f.write(json.dumps(session.to_dict(), indent=2))
            logger.info("Session saved to disk", extra={
                'user_id': telegram_id,
                'path': str(session_path),
                'message_count': len(session.messages)
            })
            return True
        except Exception as e:
            logger.error("Failed to save session to disk", extra={
                'user_id': telegram_id,
                'path': str(session_path),
                'error': str(e)
            }, exc_info=True)
            return False

    async def load_session_from_disk(self, telegram_id: int) -> bool:
        session_path = Config.get_user_session_path(telegram_id)
        if not session_path.exists():
            logger.debug("No session file found on disk", extra={'user_id': telegram_id})
            return False

        try:
            async with aiofiles.open(session_path, 'r') as f:
                data = await f.read()
                session = UserSession.from_dict(json.loads(data))
                session.agent = await self.create_agent(telegram_id)
                self.sessions[telegram_id] = session

                logger.info("Session loaded from disk", extra={
                    'user_id': telegram_id,
                    'message_count': len(session.messages),
                    'has_agent': session.agent is not None
                })

                return True
        except Exception as e:
            logger.error("Failed to load session from disk", extra={
                'user_id': telegram_id,
                'path': str(session_path),
                'error': str(e)
            }, exc_info=True)
            return False

    def clear_session(self, telegram_id: int):
        if telegram_id in self.sessions:
            message_count = len(self.sessions[telegram_id].messages)
            self.sessions[telegram_id].clear_history()
            logger.info("Session history cleared", extra={
                'user_id': telegram_id,
                'messages_cleared': message_count
            })

    def cleanup_expired_sessions(self) -> int:
        expired_users = [
            telegram_id for telegram_id, session in self.sessions.items()
            if session.is_expired()
        ]

        if expired_users:
            logger.info("Cleaning up expired sessions", extra={
                'expired_count': len(expired_users),
                'user_ids': expired_users
            })

        for telegram_id in expired_users:
            self._cleanup_session(telegram_id)

        return len(expired_users)

    def _cleanup_session(self, telegram_id: int):
        if telegram_id in self.sessions:
            logger.debug("Cleaning up session", extra={'user_id': telegram_id})
            del self.sessions[telegram_id]

    def store_auth_flow(self, state: str, telegram_id: int):
        # Cleanup expired flows before adding new one
        self.cleanup_expired_auth_flows()

        logger.debug("Storing auth flow", extra={'user_id': telegram_id})
        self.auth_flows[state] = (telegram_id, time.time())

    def get_auth_flow(self, state: str) -> Optional[int]:
        flow_data = self.auth_flows.get(state)
        if flow_data:
            telegram_id, timestamp = flow_data
            # Check if flow has expired
            if (time.time() - timestamp) > self.AUTH_FLOW_TIMEOUT:
                logger.warning("Auth flow expired", extra={
                    'user_id': telegram_id,
                    'age_seconds': time.time() - timestamp
                })
                self.remove_auth_flow(state)
                return None
            logger.debug("Auth flow retrieved", extra={'user_id': telegram_id})
            return telegram_id
        else:
            logger.warning("Auth flow not found")
        return None

    def remove_auth_flow(self, state: str):
        if state in self.auth_flows:
            telegram_id, _ = self.auth_flows[state]
            logger.debug("Removing auth flow", extra={'user_id': telegram_id})
            del self.auth_flows[state]

    def cleanup_expired_auth_flows(self) -> int:
        """Remove auth flows older than AUTH_FLOW_TIMEOUT."""
        current_time = time.time()
        expired_states = [
            state for state, (telegram_id, timestamp) in self.auth_flows.items()
            if (current_time - timestamp) > self.AUTH_FLOW_TIMEOUT
        ]

        if expired_states:
            logger.info("Cleaning up expired auth flows", extra={
                'expired_count': len(expired_states)
            })

        for state in expired_states:
            telegram_id, _ = self.auth_flows[state]
            logger.debug("Removing expired auth flow", extra={
                'user_id': telegram_id,
                'age_seconds': current_time - self.auth_flows[state][1]
            })
            del self.auth_flows[state]

        return len(expired_states)
