from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.transfer import TransferCreate


def transfer_payload():
    return {
        "source_account_id": uuid4(),
        "destination_account_id": uuid4(),
        "amount": "500.2500",
        "currency": " inr ",
        "description": "  Monthly savings ",
        "transaction_date": date(2026, 11, 7),
    }


def test_transfer_create_normalizes_currency_and_description():
    transfer = TransferCreate(**transfer_payload())

    assert transfer.currency == "INR"
    assert transfer.description == "Monthly savings"
    assert transfer.amount == Decimal("500.2500")


@pytest.mark.parametrize("amount", ["0", "-5"])
def test_transfer_create_rejects_non_positive_amount(amount):
    payload = transfer_payload()
    payload["amount"] = amount

    with pytest.raises(ValidationError):
        TransferCreate(**payload)


def test_transfer_create_rejects_blank_description():
    payload = transfer_payload()
    payload["description"] = " "

    with pytest.raises(ValidationError):
        TransferCreate(**payload)
