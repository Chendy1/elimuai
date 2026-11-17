"""Password hashing (Argon2id) and opaque token helpers."""
import hashlib
import secrets
from functools import cache

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)


@cache
def dummy_hash() -> str:
    """Used to spend comparable time when the account does not exist."""
    return _hasher.hash("not-a-real-password-for-timing")


def new_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Only the hash of a session or reset token is stored in the database."""
    return hashlib.sha256(token.encode()).hexdigest()
