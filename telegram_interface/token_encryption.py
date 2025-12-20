from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import json
import logging
from config import Config

logger = logging.getLogger(__name__)


class TokenEncryption:
    # NIST recommendation for PBKDF2 iterations (as of 2024-2025)
    PBKDF2_ITERATIONS = 480000

    def __init__(self):
        secret_key = Config.SECRET_KEY
        salt = Config.SECRET_KEY_SALT

        if not secret_key:
            raise ValueError("SECRET_KEY must be set in environment variables")

        if not salt:
            logger.warning("SECRET_KEY_SALT not set, using default (NOT RECOMMENDED for production)")
            # Use a default salt if not provided (but warn - not ideal for production)
            salt = "default_salt_please_change_in_production"

        # Use PBKDF2 for strong key derivation
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # Fernet requires 32-byte key
            salt=salt.encode(),
            iterations=self.PBKDF2_ITERATIONS,
            backend=default_backend()
        )

        key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
        self.fernet = Fernet(key)

        logger.info("TokenEncryption initialized with PBKDF2", extra={
            'iterations': self.PBKDF2_ITERATIONS,
            'has_custom_salt': Config.SECRET_KEY_SALT is not None
        })

    def encrypt(self, token: dict) -> str:
        return self.fernet.encrypt(json.dumps(token).encode()).decode()

    def decrypt(self, encrypted_token: str) -> dict:
        return json.loads(self.fernet.decrypt(encrypted_token.encode()).decode())
