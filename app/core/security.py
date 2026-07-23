"""Password hashing and JWT access token utilities.

Kept as pure functions (no DB access, no FastAPI dependencies) so the
crypto logic is trivial to unit test in isolation from the API layer.
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import bcrypt
import jwt

from app.core.config import get_settings


def hash_password(plain_password: str) -> str:
    """Hashes a plaintext password with bcrypt, returning a UTF-8 string
    safe to store in the database.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Checks a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(subject: UUID) -> str:
    """Creates a signed JWT whose `sub` claim is the user's id, expiring
    after `settings.access_token_expire_minutes`.
    """
    settings = get_settings()
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(subject), "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> UUID | None:
    """Decodes a JWT and returns the user id it was issued for, or `None`
    if the token is missing, expired, or has an invalid signature.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.InvalidTokenError:
        return None

    subject = payload.get("sub")
    if subject is None:
        return None

    try:
        return UUID(subject)
    except ValueError:
        return None


def generate_password_reset_token() -> str:
    """Generates a high-entropy, URL-safe random token to email to a user
    requesting a password reset.

    Uses `secrets` (not `random`) because this token is a bearer
    credential, same trust level as a password — it must be
    unguessable.
    """
    return secrets.token_urlsafe(32)


def hash_reset_token(raw_token: str) -> str:
    """Hashes a reset token for storage.

    Unlike passwords, reset tokens are already high-entropy random
    strings (not something a human chose), so a fast cryptographic hash
    (SHA-256) is appropriate here — there's no risk of a dictionary
    attack the way there is with bcrypt-for-passwords, and a fast hash
    keeps token lookups cheap.
    """
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
