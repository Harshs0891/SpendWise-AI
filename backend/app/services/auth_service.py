
# Import SQLAlchemy query utilities and database session types.
from sqlalchemy import select
from sqlalchemy.orm import Session

# Import password hashing utility, User model, and registration schema.
from app.core.security import hash_password
from app.models import User
from app.schemas.user import UserCreate

# Import SQLAlchemy integrity error for database constraint handling.
from sqlalchemy.exc import IntegrityError


# Register a new user after validating their registration details.
def register_user(db: Session, user_data: UserCreate) -> User:
    """
    Register a new user.

    Args:
        db: Active SQLAlchemy database session.
        user_data: Validated registration data.

    Returns:
        User: Newly created SQLAlchemy User object.

    Raises:
        ValueError: If the email is already registered.
    """

    # Normalize email to maintain consistent email identity.
    normalized_email = str(user_data.email).strip().lower()

    # Check whether a user with this email already exists.
    existing_user = db.scalar(
        select(User).where(User.email == normalized_email)
    )

    # Reject registration if the email is already registered.
    if existing_user:
        raise ValueError("An account with this email already exists.")

    # Hash the password before storing it in the database.
    hashed_password = hash_password(user_data.password)

    # Create a new SQLAlchemy User object.
    new_user = User(
        email=normalized_email,
        password_hash=hashed_password,
    )

    # Add the new user to the current database session.
    db.add(new_user)

    try:
        # Commit the transaction to persist the user in PostgreSQL.
        db.commit()

        # Refresh the object to retrieve database-generated values.
        db.refresh(new_user)

    except IntegrityError as exc:
        # Roll back the failed transaction to restore session usability.
        db.rollback()

        # Check whether the email uniqueness constraint caused the failure.
        constraint_name = getattr(
            getattr(exc.orig, "diag", None),
            "constraint_name",
            None,
        )

        if constraint_name in {"ix_users_email", "uq_users_email"}:
            # Convert duplicate email registration into a business-level error.
            raise ValueError(
                "An account with this email already exists."
            ) from exc

        # Re-raise unrelated database integrity errors.
        raise

    # Return the newly registered user.
    return new_user
