from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TransferCreate(BaseModel):
    source_account_id: UUID
    destination_account_id: UUID
    amount: Decimal = Field(gt=0, max_digits=19, decimal_places=4)
    currency: str = Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    description: str = Field(min_length=2, max_length=255)
    transaction_date: date

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.strip().upper() if isinstance(value, str) else value

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Transfer description cannot be empty.")
        return value


class TransferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    source_account_id: UUID
    destination_account_id: UUID
    amount: Decimal
    currency: str
    description: str
    transaction_date: date
    idempotency_key: str
    created_at: datetime
    debit_transaction_id: UUID
    credit_transaction_id: UUID


class TransferListResponse(BaseModel):
    items: list[TransferResponse]
    total: int
    limit: int
    offset: int
