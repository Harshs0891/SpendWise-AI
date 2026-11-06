
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt

from app.core.config import get_settings


settings = get_settings()


def create_access_token(user_id: UUID) -> str:
    """
    Create a signed JWT access token for a user.
    """

    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(
            minutes=settings.access_token_expire_minutes
        ),
    }

    token = jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.algorithm,
    )

    return token


def decode_access_token(token: str) -> dict:
    """
    Verify and decode a JWT access token.
    """

    payload = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm],
    )

    return payload
