from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user
from app.models import User
from app.schemas.user import UserResponse


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    """
    Return the profile of the currently authenticated user.
    """

    return current_user