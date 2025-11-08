import sqlite3

from .config import Config
from .token_encryption import TokenEncryption
from uuid import uuid4


class UserTokensDB:
    def __init__(self):
        self.conn = sqlite3.connect(Config.USER_TOKENS_DB, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.encryptor = TokenEncryption()
        self._create_tables()

    def _create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_tokens (
                user_id VARCHAR PRIMARY KEY,
                telegram_id INTEGER UNIQUE,
                timezone VARCHAR,
                oauth_token VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def add_user(self, telegram_id: int, oauth_token: dict):
        self.cursor.execute(
            '''
            INSERT INTO user_tokens (user_id, telegram_id, oauth_token)
            VALUES (?, ?, ?)
            ON CONFLICT(telegram_id)
            DO UPDATE SET oauth_token = ?, updated_at = CURRENT_TIMESTAMP
            ''',
            (str(uuid4()), telegram_id, self.encryptor.encrypt(oauth_token), self.encryptor.encrypt(oauth_token))
        )
        self.conn.commit()

    def get_user_token(self, telegram_id: int) -> dict | None:
        self.cursor.execute('SELECT oauth_token FROM user_tokens WHERE telegram_id = ?', (telegram_id,))
        result = self.cursor.fetchone()
        if result and result[0]:
            return self.encryptor.decrypt(result[0])
        return None
    
    def update_token(self, telegram_id: int, oauth_token: dict):
        self.cursor.execute('''
            UPDATE user_tokens
            SET oauth_token = ?, updated_at = CURRENT_TIMESTAMP
            WHERE telegram_id = ?
        ''', (self.encryptor.encrypt(oauth_token), telegram_id)
        )
        self.conn.commit()

    def delete_token(self, telegram_id: int):
        self.cursor.execute(
            '''
            UPDATE user_tokens
            SET oauth_token = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE telegram_id = ?
            ''',
            (telegram_id,)
        )
        self.conn.commit()

    def delete_user(self, telegram_id: int):
        self.cursor.execute('DELETE FROM user_tokens WHERE telegram_id = ?', (telegram_id,))
        self.conn.commit()

    def update_timezone(self, telegram_id: int, timezone: str):
        self.cursor.execute(
            '''
            UPDATE user_tokens
            SET timezone = ?
            WHERE telegram_id = ?
            ''',
            (timezone, telegram_id)
        )
        self.conn.commit()

    def get_timezone(self, telegram_id: int) -> str | None:
        self.cursor.execute('SELECT timezone FROM user_tokens WHERE telegram_id = ?', (telegram_id,))
        result = self.cursor.fetchone()
        if result and result[0]:
            return result[0]
        return None

    def close(self):
        self.conn.close()