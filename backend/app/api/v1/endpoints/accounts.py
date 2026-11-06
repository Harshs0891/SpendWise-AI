
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.account import (
    AccountCreate,
    AccountResponse,
    AccountUpdate,
)
from app.services.account_service import (
    archive_account,
    create_account,
    get_account_by_id,
    get_accounts,
    update_account,
)


router = APIRouter(
    prefix="/accounts",
    tags=["Accounts"],
)


@router.post(
    "",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_account_endpoint(
    account_data: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new account for the logged-in user.

    Example:
        POST /api/v1/accounts

    Authentication:
        Bearer token required.
    """

    return create_account(
        db=db,
        user_id=current_user.id,
        account_data=account_data,
    )


@router.get(
    "",
    response_model=list[AccountResponse],
)
def list_accounts_endpoint(
    active_only: bool = Query(default=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List accounts belonging to the logged-in user.

    Example:
        GET /api/v1/accounts?active_only=true
    """

    return get_accounts(
        db=db,
        user_id=current_user.id,
        active_only=active_only,
    )


@router.get(
    "/{account_id}",
    response_model=AccountResponse,
)
def get_account_endpoint(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a specific account owned by the logged-in user.
    """

    account = get_account_by_id(
        db=db,
        user_id=current_user.id,
        account_id=account_id,
    )

    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found.",
        )

    return account


@router.patch(
    "/{account_id}",
    response_model=AccountResponse,
)
def update_account_endpoint(
    account_id: UUID,
    account_data: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an account owned by the logged-in user.
    """

    account = update_account(
        db=db,
        user_id=current_user.id,
        account_id=account_id,
        account_data=account_data,
    )

    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found or inactive.",
        )

    return account


@router.delete(
    "/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def archive_account_endpoint(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Archive an account.

    This does not permanently delete its historical records.
    """

    archived = archive_account(
        db=db,
        user_id=current_user.id,
        account_id=account_id,
    )

    if not archived:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found or already archived.",
        )

    return None
