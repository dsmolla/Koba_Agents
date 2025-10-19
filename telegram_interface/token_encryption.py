from cryptography.fernet import Fernet
import base64
import hashlib
import json
from .config import Config


class TokenEncryption:
    def __init__(self):
        secret_key = Config.SECRET_KEY
        key = base64.urlsafe_b64encode(hashlib.sha256(secret_key.encode()).digest())
        self.fernet = Fernet(key)

    def encrypt(self, token: dict) -> str:
        return self.fernet.encrypt(json.dumps(token).encode()).decode()
    
    def decrypt(self, encrypted_token: str) -> dict:
        return json.loads(self.fernet.decrypt(encrypted_token.encode()).decode())
