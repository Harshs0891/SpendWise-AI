from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.category import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
)
from app.services.category_service import (
    create_category,
    delete_category,
    get_categories,
    get_category_by_id,
    update_category,
)


# Router for all category-related operations.
router = APIRouter()


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_category_endpoint(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a custom category for the authenticated user.

    System categories are created through the seeding process,
    not through this endpoint.
    """

    try:
        return create_category(
            db=db,
            user_id=current_user.id,
            category_data=category_data,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.get(
    "",
    response_model=list[CategoryResponse],
)
def list_categories_endpoint(
    # Optional filter for income or expense categories.
    category_kind: Literal["income", "expense"] | None = Query(
        default=None,
        alias="kind",
    ),

    # Include shared system categories by default.
    include_system: bool = Query(default=True),

    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List system categories and the user's custom categories.

    Examples:
    GET /api/v1/categories
    GET /api/v1/categories?kind=expense
    GET /api/v1/categories?kind=income
    GET /api/v1/categories?include_system=false
    """

    return get_categories(
        db=db,
        user_id=current_user.id,
        category_kind=category_kind,
        include_system=include_system,
    )


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
)
def retrieve_category_endpoint(
    category_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a category by ID.

    A user can retrieve:
    - Shared system categories.
    - Their own custom categories.

    Other users' custom categories are not accessible.
    """

    category = get_category_by_id(
        db=db,
        user_id=current_user.id,
        category_id=category_id,
    )

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found.",
        )

    return category


@router.patch(
    "/{category_id}",
    response_model=CategoryResponse,
)
def update_category_endpoint(
    category_id: UUID,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a custom category.

    System categories cannot be modified.
    """

    try:
        category = update_category(
            db=db,
            user_id=current_user.id,
            category_id=category_id,
            category_data=category_data,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Custom category not found.",
        )

    return category


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_category_endpoint(
    category_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a custom category.

    System categories cannot be deleted.

    Existing transactions referencing this category
    will have their category_id set to NULL.
    """

    deleted = delete_category(
        db=db,
        user_id=current_user.id,
        category_id=category_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Custom category not found.",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
