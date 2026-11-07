from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.transfer import TransferCreate, TransferListResponse, TransferResponse
from app.services.transfer_service import (
    create_transfer,
    get_transfer_by_id,
    get_transfers,
)

router = APIRouter()


@router.post(
    "",
    response_model=TransferResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_transfer_endpoint(
    transfer_data: TransferCreate,
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        min_length=1,
        max_length=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Move money between two owned accounts as one atomic operation."""
    try:
        return create_transfer(
            db=db,
            user_id=current_user.id,
            transfer_data=transfer_data,
            idempotency_key=idempotency_key,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.get("", response_model=TransferListResponse)
def list_transfers_endpoint(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List transfers owned by the authenticated user."""
    items, total = get_transfers(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )
    return TransferListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{transfer_id}", response_model=TransferResponse)
def retrieve_transfer_endpoint(
    transfer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve one transfer, including the IDs of its two ledger entries."""
    transfer = get_transfer_by_id(
        db=db,
        user_id=current_user.id,
        transfer_id=transfer_id,
    )
    if transfer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transfer not found.",
        )
    return transfer
