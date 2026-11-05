
# Import FastAPI utilities for routing, dependency injection, and HTTP errors.
from fastapi import APIRouter, Depends, HTTPException, status

# Import SQLAlchemy session type.
from sqlalchemy.orm import Session

# Import database dependency.
from app.db.session import get_db

# Import registration service.
from app.services.auth_service import register_user

# Import request and response schemas.
from app.schemas.user import UserCreate, UserResponse


# Create a router for authentication-related endpoints.
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# Register a new user and return their safe account details.
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    """
    Register a new SpendWise AI user.

    Args:
        user_data: Validated registration request.
        db: Database session injected by FastAPI.

    Returns:
        UserResponse: Newly registered user's public details.

    Raises:
        HTTPException: If the email is already registered.
    """

    try:
        # Delegate registration business logic to the service layer.
        new_user = register_user(db, user_data)

        # Return the newly created user.
        return new_user

    except ValueError as exc:
        # Convert duplicate registration errors into an HTTP 409 response.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
