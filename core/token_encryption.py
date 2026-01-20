from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import json
import logging
from config import Config

logger = logging.getLogger(__name__)


class TokenEncryption:
    PBKDF2_ITERATIONS = 480_000

    def __init__(self):
        secret_key = Config.SECRET_KEY
        salt_bytes = Config.SECRET_KEY_SALT.encode()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt_bytes,
            iterations=self.PBKDF2_ITERATIONS,
            backend=default_backend()
        )

        key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
        self.fernet = Fernet(key)

        logger.info(f"Encryption initialized. Iterations: {self.PBKDF2_ITERATIONS}")

    def encrypt(self, token: dict) -> str:
        try:
            json_bytes = json.dumps(token).encode('utf-8')
            return self.fernet.encrypt(json_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, encrypted_token: str) -> dict:
        try:
            decrypted_bytes = self.fernet.decrypt(encrypted_token.encode('utf-8'))
            return json.loads(decrypted_bytes.decode('utf-8'))
        except InvalidToken:
            logger.warning("Decryption failed: Invalid Token")
            return None
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None


token_encryptor = TokenEncryption()