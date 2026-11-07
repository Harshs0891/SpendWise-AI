from decimal import Decimal
from uuid import uuid4

from app.models.transaction import Transaction


def test_transaction_model_has_ledger_and_transfer_fields():
    columns = Transaction.__table__.columns

    assert {"id", "user_id", "account_id", "category_id", "transfer_id", "type", "amount", "currency", "transaction_date"} <= set(columns.keys())
    assert columns["amount"].type.precision == 19
    assert columns["amount"].type.scale == 4
    assert "ck_transactions_type" in {c.name for c in Transaction.__table__.constraints}
    assert "ck_transactions_amount_positive" in {c.name for c in Transaction.__table__.constraints}


def test_transaction_model_allows_optional_category_and_transfer():
    transaction = Transaction(
        id=uuid4(), user_id=uuid4(), account_id=uuid4(),
        category_id=None, transfer_id=None, type="expense",
        amount=Decimal("25.5000"), currency="INR",
        description="Lunch",
    )

    assert transaction.category_id is None
    assert transaction.transfer_id is None
    assert transaction.amount == Decimal("25.5000")
