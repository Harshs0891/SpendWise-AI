import pytest
from pydantic import ValidationError

from app.schemas.user import TokenResponse, UserCreate, UserLogin, UserResponse


def test_user_create_normalizes_email_and_accepts_valid_password():
    user = UserCreate(email="TEST@Example.com", password="password123")

    assert str(user.email) == "TEST@example.com"


@pytest.mark.parametrize("password", ["short", ""])
def test_user_create_rejects_short_password(password):
    with pytest.raises(ValidationError):
        UserCreate(email="user@example.com", password=password)


def test_user_login_requires_valid_email_and_password():
    login = UserLogin(email="user@example.com", password="password123")
    assert login.password == "password123"


def test_token_response_defaults_to_bearer():
    token = TokenResponse(access_token="signed-token", expires_in=1800)
    assert token.token_type == "bearer"
