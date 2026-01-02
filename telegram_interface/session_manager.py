import asyncio
import json
import logging
import shutil
import time
from collections import defaultdict
from pathlib import Path
from typing import Optional

import aiofiles
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.globals import set_debug
from langchain_core.runnables import RunnableConfig

from agents.supervisor import GoogleAgent
from agents.common.llm_models import LLM_FLASH

from .auth import AuthManager
from config import Config

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
        # Implement message trimming to prevent unbounded growth
        if len(self.messages) > Config.MAX_MESSAGE_HISTORY:
            # Keep the most recent messages
            self.messages = self.messages[-Config.MAX_MESSAGE_HISTORY:]
            logger.debug("Message history trimmed", extra={
                'user_id': self.telegram_id,
                'kept_messages': len(self.messages)
            })
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
    def __init__(self, auth_manager: 'AuthManager') -> None:
        logger.info("Initializing SessionManager")
        self.sessions: dict[int, UserSession] = {}
        self.auth_manager = auth_manager

        # Locks for thread safety
        self._session_locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)

        # Shared checkpointer for all agents (will be initialized asynchronously)
        self._checkpointer: Optional[AsyncSqliteSaver] = None

        set_debug(Config.LANGGRAPH_DEBUG)
        logger.info("SessionManager initialized successfully", extra={
            'langgraph_debug_mode': Config.LANGGRAPH_DEBUG,
            'session_timeout': Config.SESSION_TIMEOUT
        })

    async def initialize(self):
        """Initialize async resources like the checkpointer."""
        if self._checkpointer is None:
            checkpointer_path = str(Path(Config.CHECKPOINTER_DB).absolute())
            # Store the context manager separately
            self._checkpointer_cm = AsyncSqliteSaver.from_conn_string(checkpointer_path)
            # Enter the context manager to get the actual saver
            self._checkpointer = await self._checkpointer_cm.__aenter__()
            logger.info("Checkpointer initialized", extra={'db_path': checkpointer_path})

    async def close(self):
        """Clean up resources."""
        if self._checkpointer_cm:
            await self._checkpointer_cm.__aexit__(None, None, None)
            logger.info("Checkpointer closed")

    async def is_user_authenticated(self, telegram_id: int) -> bool:
        """Check if user is authenticated. Delegates to AuthManager."""
        return await self.auth_manager.is_user_authenticated(telegram_id)

    async def get_session(self, telegram_id: int) -> UserSession:
        async with self._session_locks[telegram_id]:
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
        """Create a GoogleAgent instance for the user."""
        logger.debug("Attempting to create agent", extra={'user_id': telegram_id})

        # Use AuthManager to create the API service
        google_service = await self.auth_manager.create_api_service(telegram_id)
        if google_service is None:
            logger.warning("Cannot create agent - failed to create API service", extra={'user_id': telegram_id})
            return None

        timezone = await self.auth_manager.get_user_timezone(telegram_id) or 'UTC'
        logger.info("GoogleAgent created successfully", extra={
            'user_id': telegram_id,
            'timezone': timezone
        })

        return GoogleAgent(
            google_service=google_service,
            llm=LLM_FLASH,
            config=RunnableConfig(configurable={"thread_id": telegram_id}),
            download_folder=str(Path(Config.USER_FILES_DIR) / str(telegram_id)),
            checkpointer=self._checkpointer
        )

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
            user_file_path = Config.USER_FILES_DIR / str(telegram_id)
            if user_file_path.exists() and user_file_path.is_dir():
                logger.debug("Deleting user files", extra={'user_id': telegram_id})
                shutil.rmtree(user_file_path)

    async def store_auth_flow(self, state: str, telegram_id: int, pkce_verifier: Optional[str] = None):
        """Store auth flow. Delegates to AuthManager."""
        await self.auth_manager.store_auth_flow(state, telegram_id, pkce_verifier)

    def get_auth_flow(self, state: str) -> Optional[tuple[int, Optional[str]]]:
        """Get auth flow. Delegates to AuthManager."""
        return self.auth_manager.get_auth_flow(state)

    def remove_auth_flow(self, state: str):
        """Remove auth flow. Delegates to AuthManager."""
        self.auth_manager.remove_auth_flow(state)
