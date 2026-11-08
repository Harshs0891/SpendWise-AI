
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.jwt import decode_access_token
from app.db.session import get_db
from app.models import User


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Extract and validate the JWT, then return the authenticated user.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Verify the JWT signature and expiration.
        payload = decode_access_token(token)

        # Extract the user UUID from the subject claim.
        subject = payload.get("sub")

        if not isinstance(subject, str):
            raise credentials_exception

        user_id = UUID(subject)

    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise credentials_exception from None

    # Retrieve the user using the UUID primary key.
    user = db.get(User, user_id)

    # Reject missing or inactive accounts.
    if user is None or not user.is_active:
        raise credentials_exception

    return user
