from datetime import date
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models import User
from app.services.csv_transaction_service import (
    CSVImportValidationError,
    export_transactions_to_csv,
    import_transactions_from_csv,
)


router = APIRouter()
MAX_CSV_BYTES = 5 * 1024 * 1024


@router.get("/export")
def export_transactions_csv_endpoint(
    transaction_type: Literal["income", "expense"] | None = Query(default=None, alias="type"),
    account_id: UUID | None = None,
    category_id: UUID | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download the authenticated user's ordinary transactions as CSV."""
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_date cannot be later than end_date.",
        )

    content = export_transactions_to_csv(
        db=db,
        user_id=current_user.id,
        transaction_type=transaction_type,
        account_id=account_id,
        category_id=category_id,
        start_date=start_date,
        end_date=end_date,
    )
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="spendwise_transactions.csv"'},
    )


@router.post("/import", status_code=status.HTTP_200_OK)
async def import_transactions_csv_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Validate and atomically import transactions from a CSV upload."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload a .csv file.",
        )

    raw_content = await file.read(MAX_CSV_BYTES + 1)
    if len(raw_content) > MAX_CSV_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="CSV file exceeds the 5 MB upload limit.",
        )

    try:
        csv_text = raw_content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV must use UTF-8 encoding.",
        ) from error
    finally:
        await file.close()

    try:
        return import_transactions_from_csv(
            db=db,
            user_id=current_user.id,
            csv_text=csv_text,
        )
    except CSVImportValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": str(error),
                "row_errors": error.errors,
            },
        ) from error
