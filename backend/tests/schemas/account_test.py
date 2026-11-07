from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.account import AccountCreate, AccountResponse, AccountUpdate


def test_account_create_applies_currency_and_balance_defaults():
    account = AccountCreate(name="Savings", account_type="bank")

    assert account.currency == "INR"
    assert account.opening_balance == Decimal("0.0000")


@pytest.mark.parametrize("account_type", ["invalid", "current"])
def test_account_create_rejects_unsupported_account_type(account_type):
    with pytest.raises(ValidationError):
        AccountCreate(name="Savings", account_type=account_type)


@pytest.mark.parametrize("currency", ["inr", "US", "INR1"])
def test_account_create_rejects_invalid_currency(currency):
    with pytest.raises(ValidationError):
        AccountCreate(name="Savings", account_type="bank", currency=currency)


def test_account_update_allows_name_only():
    assert AccountUpdate(name="New name").name == "New name"
    assert AccountUpdate().model_dump(exclude_unset=True) == {}


def test_account_response_reads_orm_attributes():
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    payload = dict(
        id=uuid4(), user_id=uuid4(), name="Savings",
        account_type="bank", currency="INR",
        opening_balance=Decimal("1.0000"), is_active=True,
        created_at=now, updated_at=now,
    )

    assert AccountResponse.model_validate(payload).name == "Savings"
