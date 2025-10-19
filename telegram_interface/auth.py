from datetime import datetime, timezone
import json
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


from .config import Config
from .user_tokens_db import UserTokensDB


class AuthManager:
    def __init__(self):
        self.user_tokens_db = UserTokensDB()
    
    def create_flow(self, state: str) -> Flow:
        flow = Flow.from_client_secrets_file(
            Config.CREDS_PATH,
            scopes=Config.OAUTH_SCOPES,
            redirect_uri=Config.OAUTH_REDIRECT_URI,
            state=state
        )
        return flow

    def generate_auth_url(self, state: str) -> str:
        flow = self.create_flow(state=state)

        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
        )

        return auth_url

    def complete_auth(self, state: str, telegram_id: int, code: str) -> bool:
        flow = self.create_flow(state)
        flow.fetch_token(code=code)

        if not flow.credentials:
            return False

        self.user_tokens_db.add_user(telegram_id, json.loads(flow.credentials.to_json()))
        return True

    def user_authenticated(self, telegram_id: int) -> bool:
        token = self.user_tokens_db.get_user_token(telegram_id)
        return token is not None
  
    def invalidate_token(self, telegram_id: int):
        with self.user_tokens_db.lock:
            self.user_tokens_db.cursor.execute('''
                UPDATE user_tokens
                SET token_data = NULL
                WHERE telegram_id = ?
            ''', (datetime.now(timezone.utc), telegram_id)
            )
            self.user_tokens_db.conn.commit()
    
    def refresh_token(self, telegram_id: int) -> bool:
        token = self.user_tokens_db.get_user_token(telegram_id)
        if not token:
            return False
        
        creds = Credentials.from_authorized_user_info(token, Config.OAUTH_SCOPES)
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                self.user_tokens_db.add_user(telegram_id, json.loads(creds.to_json()))
                return True
            except Exception as e:
                print(f"Error refreshing token for user {telegram_id}: {e}")
                return False
        return False
    
            


        