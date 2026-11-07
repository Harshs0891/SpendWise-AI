from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.models.transfer import Transfer


def test_transfer_model_declares_idempotency_and_integrity_constraints():
    constraints = {c.name for c in Transfer.__table__.constraints}

    assert "uq_transfers_user_id_idempotency_key" in constraints
    assert "ck_transfers_amount_positive" in constraints
    assert "ck_transfers_distinct_accounts" in constraints


def test_transfer_model_can_be_instantiated():
    transfer = Transfer(
        id=uuid4(), user_id=uuid4(),
        source_account_id=uuid4(), destination_account_id=uuid4(),
        amount=Decimal("500.0000"), currency="INR",
        description="Savings transfer",
        transaction_date=date(2026, 11, 7),
        idempotency_key="request-123",
    )

    assert transfer.amount == Decimal("500.0000")
    assert transfer.idempotency_key == "request-123"
