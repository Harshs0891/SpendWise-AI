from decimal import Decimal
from uuid import uuid4

from app.models.account import Account


def test_account_model_columns_and_constraints():
    assert {"id", "user_id", "name", "account_type", "currency", "opening_balance", "is_active"} <= set(Account.__table__.columns.keys())
    constraints = {constraint.name for constraint in Account.__table__.constraints}
    assert "ck_accounts_account_type" in constraints
    assert "ck_accounts_currency_length" in constraints
    assert "ix_accounts_user_id_is_active" in {index.name for index in Account.__table__.indexes}


def test_account_model_preserves_decimal_values():
    account = Account(
        id=uuid4(), user_id=uuid4(), name="Savings",
        account_type="bank", currency="INR",
        opening_balance=Decimal("1234.5600"),
    )

    assert account.opening_balance == Decimal("1234.5600")
