
import os

from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv

load_dotenv()


def get_fernet():
    key = os.getenv("DB_ENCRYPTION_KEY")

    if not key:
        raise RuntimeError(
            "DB_ENCRYPTION_KEY is missing from environment variables."
        )

    try:
        return Fernet(key.encode("utf-8"))
    except (ValueError, TypeError) as exc:
        raise RuntimeError(
            "DB_ENCRYPTION_KEY is invalid."
        ) from exc


def encrypt_password(password: str) -> str:
    if not isinstance(password, str) or not password:
        raise ValueError("Password must be a non-empty string.")

    fernet = get_fernet()
    encrypted = fernet.encrypt(password.encode("utf-8"))

    return encrypted.decode("utf-8")


def decrypt_password(encrypted_password: str) -> str:
    if not encrypted_password:
        raise ValueError("Encrypted password is empty.")

    fernet = get_fernet()

    try:
        decrypted = fernet.decrypt(
            encrypted_password.encode("utf-8")
        )
        return decrypted.decode("utf-8")
    except (InvalidToken, ValueError) as exc:
        raise ValueError(
            "Could not decrypt the saved database password. "
            "Check the encryption key."
        ) from exc
