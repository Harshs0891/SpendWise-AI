
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """
    Schema for incoming user registration requests.
    """

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
        description="User password (minimum 8 and maximum 128 characters)",
    )


class UserResponse(BaseModel):
    """
    Schema for user data returned by the API.

    Sensitive fields such as password and password_hash
    are intentionally excluded.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    is_active: bool
    created_at: datetime
    updated_at: datetime
