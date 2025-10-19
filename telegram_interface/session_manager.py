import json
import time
from typing import Optional

from google_auth_oauthlib.flow import Flow

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage

from google_agent.agent import GoogleAgent
from google_agent.shared.llm_models import LLM_FLASH
from google_client.user_client import UserClient
from .auth import AuthManager

from .config import Config


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

    def add_messages(self, message: list[BaseMessage]):
        self.messages.extend(message)
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
        session.last_activity = data['last_activity']

        for msg_data in data['messages']:
            if msg_data['type'] == HumanMessage:
                session.messages.append(
                    HumanMessage(content=msg_data['content']))
            elif msg_data['type'] == 'AIMessage':
                session.messages.append(AIMessage(content=msg_data['content']))
            elif msg_data['type'] == 'ToolMessage':
                session.messages.append(
                    ToolMessage(content=msg_data['content']))

        return session


class SessionManager:
    def __init__(self) -> None:
        self.sessions: dict[int, UserSession] = {}
        self.auth_manager = AuthManager()
        self.auth_flows: dict[str, int] = {}

    def get_session(self, telegram_id: int) -> UserSession:
        if telegram_id in self.sessions:
            session = self.sessions[telegram_id]
            if session.is_expired():
                self._cleanup_session(telegram_id)
            else:
                session.update_activity()
                return session

        session = UserSession(telegram_id)
        session.agent = self.create_agent(telegram_id)
        self.sessions[telegram_id] = session
        return session

    def create_agent(self, telegram_id: int) -> Optional[GoogleAgent]:
        if not self.auth_manager.user_authenticated(telegram_id):
            return None

        google_token = self.auth_manager.user_tokens_db.get_user_token(
            telegram_id)

        if Config.CREDS_PATH is None:
            raise ValueError("Environment Variable CREDS_PATH not set")

        with open(Config.CREDS_PATH, 'r') as f:
            creds_data = json.loads(f.read())

        google_client = UserClient.from_credentials_info(
            creds_data, google_token, scopes=Config.OAUTH_SCOPES)

        agent = GoogleAgent(
            google_service=google_client[0],
            llm=LLM_FLASH,
            print_steps=Config.PRINT_STEPS
        )
        
        return agent

    def save_session_to_disk(self, telegram_id: int) -> bool:
        session = self.sessions.get(telegram_id)
        if session is None:
            return False

        if session.is_expired():
            return False

        session_path = Config.get_user_session_path(telegram_id)
        try:
            with open(session_path, 'w') as f:
                json.dump(session.to_dict(), f, indent=2)
            return True
        except Exception:
            return False

    def load_session_from_disk(self, telegram_id: int) -> bool:
        session_path = Config.get_user_session_path(telegram_id)
        if not session_path.exists():
            return False

        try:
            with open(session_path, 'r') as f:
                data = json.load(f)
                session = UserSession.from_dict(data)

                if not session.is_expired():
                    self.sessions[telegram_id] = session
                    return True
                else:
                    return False
        except Exception:
            return False

    def clear_session(self, telegram_id: int):
        if telegram_id in self.sessions:
            self.sessions[telegram_id].clear_history()

    def cleanup_expired_sessions(self):
        expired_users = [
            telegram_id for telegram_id, session in self.sessions.items()
            if session.is_expired()
        ]

        for telegram_id in expired_users:
            self._cleanup_session(telegram_id)

    def _cleanup_session(self, telegram_id: int):
        if telegram_id in self.sessions:
            del self.sessions[telegram_id]

    def store_auth_flow(self, state: str, telegram_id: int):
        self.auth_flows[state] = telegram_id

    def get_auth_flow(self, state: str) -> Optional[int]:
        return self.auth_flows.get(state)

    def remove_auth_flow(self, state: str):
        if state in self.auth_flows:
            del self.auth_flows[state]


