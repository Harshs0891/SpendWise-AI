
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.jwt import create_access_token
from app.core.security import verify_password
from app.models import User
from app.schemas.user import UserLogin


def authenticate_user(db: Session, user_data: UserLogin) -> str:
    """
    Authenticate a user and generate a JWT access token.

    Args:
        db: Active SQLAlchemy database session.
        user_data: Validated login credentials.

    Returns:
        str: Generated JWT access token.

    Raises:
        ValueError: If credentials are invalid or the account is inactive.
    """

    # Normalize email to maintain consistent email identity.
    normalized_email = str(user_data.email).strip().lower()

    # Find the user using their normalized email.
    user = db.scalar(
        select(User).where(User.email == normalized_email)
    )

    # Reject authentication if the user does not exist.
    if not user:
        raise ValueError("Invalid email or password.")

    # Verify the submitted password against the stored Argon2 hash.
    if not verify_password(user_data.password, user.password_hash):
        raise ValueError("Invalid email or password.")

    # Reject inactive accounts.
    if not user.is_active:
        raise ValueError("Invalid email or password.")

    # Generate an access token after successful authentication.
    access_token = create_access_token(user.id)

    return access_token
