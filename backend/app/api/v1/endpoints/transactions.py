
from datetime import date
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
    TransactionListResponse,
)
from app.services.transaction_service import (
    create_transaction,
    get_transaction_by_id,
    get_transactions,
    update_transaction,
)


# Router containing all transaction-related endpoints.
router = APIRouter()


@router.post(
    "",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_transaction_endpoint(
    transaction_data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create an income or expense transaction.

    The user ID is obtained from the authenticated JWT,
    never from the request body.

    The service layer validates:
    - Account ownership and active status.
    - Account currency.
    - Category existence and ownership.
    - Category type compatibility.
    """

    try:
        transaction = create_transaction(
            db=db,
            user_id=current_user.id,
            transaction_data=transaction_data,
        )

        return transaction

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.get(
    "",
    response_model=TransactionListResponse,
)
def list_transactions_endpoint(
    # Filter transactions by income or expense.
    transaction_type: Literal["income", "expense"] | None = Query(
        default=None,
        alias="type",
    ),

    # Optional account and category filters.
    account_id: UUID | None = None,
    category_id: UUID | None = None,

    # Optional date range filters.
    start_date: date | None = None,
    end_date: date | None = None,

    # Pagination parameters.
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),

    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List the authenticated user's transactions.

    Supports filtering by:
    - Transaction type.
    - Account.
    - Category.
    - Start and end dates.

    Supports pagination through limit and offset.

    Example:
    GET /api/v1/transactions?type=expense&limit=10&offset=0
    """

    # Ensure the date range is valid.
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_date cannot be later than end_date.",
        )

    # The service returns both the requested page and
    # the total number of matching transactions.
    transactions, total = get_transactions(
        db=db,
        user_id=current_user.id,
        transaction_type=transaction_type,
        account_id=account_id,
        category_id=category_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )

    # Return pagination metadata along with the transactions.
    return TransactionListResponse(
        items=transactions,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
)
def retrieve_transaction_endpoint(
    transaction_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve one transaction owned by the authenticated user.

    Transactions belonging to other users are not accessible.
    """

    transaction = get_transaction_by_id(
        db=db,
        user_id=current_user.id,
        transaction_id=transaction_id,
    )

    # Return 404 if the transaction does not exist
    # or does not belong to the authenticated user.
    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found.",
        )

    return transaction


@router.patch(
    "/{transaction_id}",
    response_model=TransactionResponse,
)
def update_transaction_endpoint(
    transaction_id: UUID,
    transaction_data: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Partially update an existing transaction.

    Only the fields supplied in the request body
    will be updated.

    The service layer validates the resulting account,
    category, transaction type, and currency.
    """

    try:
        transaction = update_transaction(
            db=db,
            user_id=current_user.id,
            transaction_id=transaction_id,
            transaction_data=transaction_data,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    # Return 404 if the transaction does not exist
    # or belongs to another user.
    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found.",
        )

    return transaction
