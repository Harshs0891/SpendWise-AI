from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


# Only two transaction types are supported in our initial MVP.
TransactionType = Literal["income", "expense"]


class TransactionCreate(BaseModel):
    """
    Request schema used when creating a transaction.

    Example:
    {
        "account_id": "account-uuid",
        "category_id": "category-uuid",
        "type": "expense",
        "amount": "500.0000",
        "currency": "INR",
        "description": "Grocery shopping",
        "merchant": "DMart",
        "transaction_date": "2026-11-06",
        "notes": "Weekly groceries"
    }
    """

    # Account to which this transaction belongs.
    # The service layer verifies account ownership.
    account_id: UUID

    # Category is optional.
    category_id: UUID | None = None

    # Only income and expense are supported.
    type: TransactionType

    # Decimal avoids floating-point precision errors.
    # Amount must always be greater than zero.
    amount: Decimal = Field(
        gt=0,
        max_digits=19,
        decimal_places=4,
    )

    # Three-character ISO currency code.
    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
    )

    description: str = Field(
        min_length=2,
        max_length=255,
    )

    merchant: str | None = Field(
        default=None,
        max_length=150,
    )

    transaction_date: date

    notes: str | None = None

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        """Convert currency codes to uppercase before validation."""
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        """Remove unnecessary whitespace and reject blank descriptions."""
        value = value.strip()

        if not value:
            raise ValueError("Transaction description cannot be empty.")

        return value

    @field_validator("merchant")
    @classmethod
    def validate_merchant(cls, value: str | None) -> str | None:
        """Normalize optional merchant names."""
        if value is not None:
            value = value.strip()

            if not value:
                return None

        return value


class TransactionUpdate(BaseModel):
    """
    Request schema for partially updating a transaction.

    Every field is optional because PATCH should modify
    only the fields supplied by the client.
    """

    account_id: UUID | None = None
    category_id: UUID | None = None

    type: TransactionType | None = None

    amount: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=19,
        decimal_places=4,
    )

    currency: str | None = Field(
        default=None,
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
    )

    description: str | None = Field(
        default=None,
        min_length=2,
        max_length=255,
    )

    merchant: str | None = Field(
        default=None,
        max_length=150,
    )

    transaction_date: date | None = None

    notes: str | None = None

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        """Normalize currency codes before pattern validation."""
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        """Reject blank descriptions while allowing omitted fields."""
        if value is not None:
            value = value.strip()

            if not value:
                raise ValueError("Transaction description cannot be empty.")

        return value

    @field_validator("merchant")
    @classmethod
    def validate_merchant(cls, value: str | None) -> str | None:
        """Convert blank merchant names to None."""
        if value is not None:
            value = value.strip()

            if not value:
                return None

        return value


class TransactionResponse(BaseModel):
    """
    Response schema returned to the client.

    from_attributes=True allows Pydantic to construct this
    response directly from a SQLAlchemy model instance.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    account_id: UUID
    category_id: UUID | None

    type: TransactionType
    amount: Decimal
    currency: str

    description: str
    merchant: str | None

    transaction_date: date
    notes: str | None

    created_at: datetime
    updated_at: datetime


class TransactionListResponse(BaseModel):
    """
    Paginated response schema for listing transactions.

    items  : Transactions returned on the current page.
    total  : Total matching transactions across all pages.
    limit  : Maximum number of records requested.
    offset : Number of records skipped.
    """

    items: list[TransactionResponse]
    total: int
    limit: int
    offset: int
