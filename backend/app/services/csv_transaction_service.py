import csv
from io import StringIO
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models import Transaction
from app.schemas.transaction import TransactionCreate
from app.services.transaction_service import validate_transaction_references


REQUIRED_HEADERS = {
    "account_id",
    "type",
    "amount",
    "currency",
    "description",
    "transaction_date",
}
OPTIONAL_HEADERS = {"category_id", "merchant", "notes"}
ALLOWED_HEADERS = REQUIRED_HEADERS | OPTIONAL_HEADERS


class CSVImportValidationError(ValueError):
    def __init__(self, errors: list[dict]):
        self.errors = errors
        super().__init__("CSV contains invalid rows. No transactions were imported.")


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def import_transactions_from_csv(
    db: Session,
    user_id: UUID,
    csv_text: str,
) -> dict:
    """
    Validate the complete CSV before inserting anything.
    Import is atomic: one invalid row rejects the entire file.
    """
    reader = csv.DictReader(StringIO(csv_text))

    if not reader.fieldnames:
        raise CSVImportValidationError([{"row": 1, "errors": ["CSV header row is missing."]}])

    headers = [header.strip() if header else "" for header in reader.fieldnames]
    if len(headers) != len(set(headers)):
        raise CSVImportValidationError([{"row": 1, "errors": ["CSV contains duplicate column names."]}])

    reader.fieldnames = headers
    missing = sorted(REQUIRED_HEADERS - set(headers))
    unknown = sorted(set(headers) - ALLOWED_HEADERS)

    header_errors = []
    if missing:
        header_errors.append(f"Missing required columns: {', '.join(missing)}.")
    if unknown:
        header_errors.append(f"Unsupported columns: {', '.join(unknown)}.")
    if header_errors:
        raise CSVImportValidationError([{"row": 1, "errors": header_errors}])

    pending: list[Transaction] = []
    errors: list[dict] = []
    data_row_count = 0

    for row_number, row in enumerate(reader, start=2):
        if not row or not any((value or "").strip() for value in row.values() if isinstance(value, str)):
            continue

        data_row_count += 1
        if None in row:
            errors.append({"row": row_number, "errors": ["Row contains more values than the header."]})
            continue

        payload = {key: (value.strip() if isinstance(value, str) else value) for key, value in row.items()}
        payload["category_id"] = _clean_optional(payload.get("category_id"))
        payload["merchant"] = _clean_optional(payload.get("merchant"))
        payload["notes"] = _clean_optional(payload.get("notes"))

        try:
            transaction_data = TransactionCreate.model_validate(payload)
            validate_transaction_references(
                db=db,
                user_id=user_id,
                account_id=transaction_data.account_id,
                category_id=transaction_data.category_id,
                transaction_type=transaction_data.type,
                currency=transaction_data.currency,
            )
            pending.append(
                Transaction(
                    user_id=user_id,
                    account_id=transaction_data.account_id,
                    category_id=transaction_data.category_id,
                    type=transaction_data.type,
                    amount=transaction_data.amount,
                    currency=transaction_data.currency,
                    description=transaction_data.description,
                    merchant=transaction_data.merchant,
                    transaction_date=transaction_data.transaction_date,
                    notes=transaction_data.notes,
                )
            )
        except ValidationError as error:
            errors.append({
                "row": row_number,
                "errors": [
                    f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}"
                    for item in error.errors()
                ],
            })
        except ValueError as error:
            errors.append({"row": row_number, "errors": [str(error)]})

    if data_row_count == 0:
        raise CSVImportValidationError([{"row": 1, "errors": ["CSV contains no transaction rows."]}])

    if errors:
        raise CSVImportValidationError(errors[:100])

    try:
        db.add_all(pending)
        db.commit()
        for transaction in pending:
            db.refresh(transaction)
    except Exception:
        db.rollback()
        raise

    return {
        "imported_count": len(pending),
        "transaction_ids": [str(transaction.id) for transaction in pending],
    }


def export_transactions_to_csv(
    db: Session,
    user_id: UUID,
    transaction_type: str | None = None,
    account_id: UUID | None = None,
    category_id: UUID | None = None,
    start_date=None,
    end_date=None,
) -> str:
    statement = select(Transaction).where(
        Transaction.user_id == user_id,
        Transaction.transfer_id.is_(None),
    )

    if transaction_type:
        statement = statement.where(Transaction.type == transaction_type)
    if account_id:
        statement = statement.where(Transaction.account_id == account_id)
    if category_id:
        statement = statement.where(Transaction.category_id == category_id)
    if start_date:
        statement = statement.where(Transaction.transaction_date >= start_date)
    if end_date:
        statement = statement.where(Transaction.transaction_date <= end_date)

    statement = statement.order_by(
        Transaction.transaction_date.desc(),
        Transaction.created_at.desc(),
    )
    transactions = db.scalars(statement).all()

    output = StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow([
        "id", "account_id", "category_id", "type", "amount", "currency",
        "description", "merchant", "transaction_date", "notes",
    ])

    def safe_cell(value):
        if value is None:
            return ""
        text = str(value)
        if text.startswith(("=", "+", "-", "@", "\t", "\r")):
            return "'" + text
        return text

    for transaction in transactions:
        writer.writerow([
            str(transaction.id),
            str(transaction.account_id),
            str(transaction.category_id) if transaction.category_id else "",
            transaction.type,
            str(transaction.amount),
            transaction.currency,
            safe_cell(transaction.description),
            safe_cell(transaction.merchant),
            transaction.transaction_date.isoformat(),
            safe_cell(transaction.notes),
        ])

    return "\ufeff" + output.getvalue()
