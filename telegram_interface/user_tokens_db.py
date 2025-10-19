import sqlite3
import threading
from .config import Config
from .token_encryption import TokenEncryption
from uuid import uuid4


class UserTokensDB:
    def __init__(self):
        self.conn = sqlite3.connect(Config.USER_TOKENS_DB, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.encryptor = TokenEncryption()
        self.lock = threading.Lock()
        self._create_tables()

    def _create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_tokens (
                user_id TEXT PRIMARY KEY,
                telegram_id INTEGER UNIQUE,
                token_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            )
        ''')
        self.conn.commit()

    def add_user(self, telegram_id: int, token_data: dict):
        with self.lock:
            self.cursor.execute('''
                INSERT OR REPLACE INTO user_tokens (user_id, telegram_id, token_data)
                VALUES (?, ?, ?)
                ON CONFLICT(telegram_id)
                DO UPDATE SET token_data = ?, updated_at = CURRENT_TIMESTAMP
            ''', (str(uuid4()), telegram_id, self.encryptor.encrypt(token_data), self.encryptor.encrypt(token_data))
            )
            self.conn.commit()

    def get_user_token(self, telegram_id: int) -> dict | None:
        with self.lock:
            self.cursor.execute('SELECT token_data FROM user_tokens WHERE telegram_id = ?', (telegram_id,))
            result = self.cursor.fetchone()
            if result and result[0]:
                return self.encryptor.decrypt(result[0])
            return None
    
    def update_token(self, telegram_id: int, token_data: dict):
        with self.lock:
            self.cursor.execute('''
                UPDATE user_tokens
                SET token_data = ?, updated_at = CURRENT_TIMESTAMP
                WHERE telegram_id = ?
            ''', (self.encryptor.encrypt(token_data), telegram_id)
            )
            self.conn.commit()

    def delete_user(self, telegram_id: int):
        with self.lock:
            self.cursor.execute('DELETE FROM user_tokens WHERE telegram_id = ?', (telegram_id,))
            self.conn.commit()

    def close(self):
        self.conn.close()