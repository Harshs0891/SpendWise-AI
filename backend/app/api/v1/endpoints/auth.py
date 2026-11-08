from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.user import (
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.auth_service import register_user
from app.services.login_service import authenticate_user


settings = get_settings()


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



@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
def login(
    user_data: UserLogin,
    db: Session = Depends(get_db),
):
    """
    Authenticate a user and return a JWT access token.
    """

    try:
        # Authenticate the user and generate an access token.
        access_token = authenticate_user(db, user_data)

        # Return the authentication response.
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc



@router.post(
    "/token",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
def swagger_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    OAuth2 form-compatible login endpoint for Swagger UI.

    The OAuth2 username field contains the user's email address.
    The existing JSON login endpoint remains unchanged.
    """

    try:
        user_data = UserLogin(
            email=form_data.username,
            password=form_data.password,
        )

        access_token = authenticate_user(db, user_data)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc