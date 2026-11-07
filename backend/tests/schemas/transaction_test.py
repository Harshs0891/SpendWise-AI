from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.transaction import TransactionCreate, TransactionUpdate


def valid_transaction_payload():
    return {
        "account_id": uuid4(),
        "type": "expense",
        "amount": "125.5000",
        "currency": " inr ",
        "description": "  Groceries  ",
        "transaction_date": date(2026, 11, 7),
    }


def test_transaction_create_normalizes_currency_and_description():
    transaction = TransactionCreate(**valid_transaction_payload())

    assert transaction.currency == "INR"
    assert transaction.description == "Groceries"
    assert transaction.amount == Decimal("125.5000")


@pytest.mark.parametrize("amount", ["0", "-1"])
def test_transaction_create_rejects_non_positive_amount(amount):
    payload = valid_transaction_payload()
    payload["amount"] = amount

    with pytest.raises(ValidationError):
        TransactionCreate(**payload)


def test_transaction_create_rejects_blank_description():
    payload = valid_transaction_payload()
    payload["description"] = "  "

    with pytest.raises(ValidationError):
        TransactionCreate(**payload)


def test_transaction_update_preserves_only_supplied_fields():
    update = TransactionUpdate(description=" Updated ")
    assert update.model_dump(exclude_unset=True) == {"description": "Updated"}


def test_transaction_update_converts_blank_merchant_to_none():
    assert TransactionUpdate(merchant=" ").merchant is None
