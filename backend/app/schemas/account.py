
from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# Only these five account types are supported in our MVP.
AccountType = Literal[
    "cash",
    "bank",
    "savings",
    "wallet",
    "credit_card",
]


class AccountCreate(BaseModel):
    """
    Schema used when a user creates a new financial account.

    Example request:
    {
        "name": "HDFC Savings",
        "account_type": "bank",
        "currency": "INR",
        "opening_balance": "25000.00"
    }
    """

    name: str = Field(
        min_length=2,
        max_length=100,
        description="User-friendly account name",
    )

    account_type: AccountType

    # Three uppercase characters representing an ISO currency code.
    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
    )

    # Decimal avoids floating-point precision errors.
    # ge=0 prevents negative opening balances in this MVP.
    opening_balance: Decimal = Field(
        default=Decimal("0.0000"),
        ge=0,
        max_digits=19,
        decimal_places=4,
    )


class AccountUpdate(BaseModel):
    """
    Schema for updating an existing account.

    For now, only the account name can be changed.

    We deliberately do not allow changing currency or account_type
    after creation because those fields affect financial semantics
    and may be referenced by future transactions.
    """

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )


class AccountResponse(BaseModel):
    """
    Safe response schema returned to the client.

    Never return an entire ORM object without defining which
    fields are allowed to leave the backend.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    account_type: AccountType
    currency: str
    opening_balance: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
