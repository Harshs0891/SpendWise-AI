from uuid import UUID
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Account, Transaction, Transfer
from app.schemas.transfer import TransferCreate


def _transfer_response_data(db: Session, transfer: Transfer) -> dict:
    """Build response-only ledger references for a transfer."""
    entries = list(
        db.scalars(
            select(Transaction)
            .where(
                Transaction.transfer_id == transfer.id,
                Transaction.user_id == transfer.user_id,
            )
            .order_by(Transaction.type)
        ).all()
    )
    debit = next((item for item in entries if item.type == "expense"), None)
    credit = next((item for item in entries if item.type == "income"), None)

    if debit is None or credit is None:
        raise RuntimeError("Transfer ledger entries are incomplete.")

    return {
        "id": transfer.id,
        "user_id": transfer.user_id,
        "source_account_id": transfer.source_account_id,
        "destination_account_id": transfer.destination_account_id,
        "amount": transfer.amount,
        "currency": transfer.currency,
        "description": transfer.description,
        "transaction_date": transfer.transaction_date,
        "idempotency_key": transfer.idempotency_key,
        "created_at": transfer.created_at,
        "debit_transaction_id": debit.id,
        "credit_transaction_id": credit.id,
    }


def create_transfer(
    db: Session,
    user_id: UUID,
    transfer_data: TransferCreate,
    idempotency_key: str,
) -> dict:
    """
    Create a transfer and its two ledger entries atomically.

    Account rows are locked in UUID order to serialize competing
    transfers and reduce deadlock risk. This MVP permits overdrafts;
    insufficient-funds enforcement is deliberately not inferred.
    """
    key = idempotency_key.strip()
    if not key or len(key) > 100:
        raise ValueError("Idempotency-Key must contain 1 to 100 characters.")

    existing = db.scalar(
        select(Transfer).where(
            Transfer.user_id == user_id,
            Transfer.idempotency_key == key,
        )
    )
    if existing is not None:
        if (
            existing.source_account_id != transfer_data.source_account_id
            or existing.destination_account_id != transfer_data.destination_account_id
            or existing.amount != transfer_data.amount
            or existing.currency != transfer_data.currency
            or existing.description != transfer_data.description
            or existing.transaction_date != transfer_data.transaction_date
        ):
            raise ValueError("Idempotency-Key was already used with a different request.")
        return _transfer_response_data(db, existing)

    if transfer_data.source_account_id == transfer_data.destination_account_id:
        raise ValueError("Source and destination accounts must be different.")

    account_ids = sorted(
        [transfer_data.source_account_id, transfer_data.destination_account_id],
        key=str,
    )
    locked_accounts = list(
        db.scalars(
            select(Account)
            .where(
                Account.id.in_(account_ids),
                Account.user_id == user_id,
                Account.is_active.is_(True),
            )
            .order_by(Account.id)
            .with_for_update()
        ).all()
    )
    if len(locked_accounts) != 2:
        raise ValueError("One or both accounts were not found, are inactive, or do not belong to you.")

    accounts_by_id = {account.id: account for account in locked_accounts}
    source = accounts_by_id[transfer_data.source_account_id]
    destination = accounts_by_id[transfer_data.destination_account_id]

    if source.currency != destination.currency:
        raise ValueError("Transfers between accounts with different currencies are not supported.")
    if source.currency != transfer_data.currency:
        raise ValueError(f"Transfer currency must match both account currencies ({source.currency}).")

    transfer = Transfer(
        user_id=user_id,
        source_account_id=source.id,
        destination_account_id=destination.id,
        amount=transfer_data.amount,
        currency=transfer_data.currency,
        description=transfer_data.description,
        transaction_date=transfer_data.transaction_date,
        idempotency_key=key,
    )

    try:
        db.add(transfer)
        db.flush()

        debit = Transaction(
            user_id=user_id,
            account_id=source.id,
            transfer_id=transfer.id,
            type="expense",
            amount=transfer_data.amount,
            currency=transfer_data.currency,
            description=f"Transfer to {destination.name}: {transfer_data.description}",
            transaction_date=transfer_data.transaction_date,
        )
        credit = Transaction(
            user_id=user_id,
            account_id=destination.id,
            transfer_id=transfer.id,
            type="income",
            amount=transfer_data.amount,
            currency=transfer_data.currency,
            description=f"Transfer from {source.name}: {transfer_data.description}",
            transaction_date=transfer_data.transaction_date,
        )

        db.add_all([debit, credit])
        db.flush()
        db.commit()
        db.refresh(transfer)

    except IntegrityError:
        db.rollback()
        # A concurrent request may have won the unique idempotency-key race.
        existing = db.scalar(
            select(Transfer).where(
                Transfer.user_id == user_id,
                Transfer.idempotency_key == key,
            )
        )
        if existing is not None:
            if (
                existing.source_account_id == transfer_data.source_account_id
                and existing.destination_account_id == transfer_data.destination_account_id
                and existing.amount == transfer_data.amount
                and existing.currency == transfer_data.currency
                and existing.description == transfer_data.description
                and existing.transaction_date == transfer_data.transaction_date
            ):
                return _transfer_response_data(db, existing)
            raise ValueError("Idempotency-Key was already used with a different request.")
        raise
    except Exception:
        db.rollback()
        raise

    return _transfer_response_data(db, transfer)
