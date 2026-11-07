from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class BudgetCreate(BaseModel):
    category_id: UUID
    amount: Decimal = Field(gt=0, max_digits=19, decimal_places=4)
    currency: str = Field(default="INR", min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    period_start: date
    alert_threshold: int = Field(default=80, ge=1, le=100)

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.strip().upper() if isinstance(value, str) else value

    @field_validator("period_start")
    @classmethod
    def require_first_day_of_month(cls, value: date) -> date:
        if value.day != 1:
            raise ValueError("period_start must be the first day of a month.")
        return value


class BudgetUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0, max_digits=19, decimal_places=4)
    alert_threshold: int | None = Field(default=None, ge=1, le=100)

    @model_validator(mode="after")
    def validate_changes(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")
        if "amount" in self.model_fields_set and self.amount is None:
            raise ValueError("amount cannot be null.")
        if "alert_threshold" in self.model_fields_set and self.alert_threshold is None:
            raise ValueError("alert_threshold cannot be null.")
        return self


class BudgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    category_id: UUID
    amount: Decimal
    currency: str
    period_start: date
    alert_threshold: int
    created_at: datetime
    updated_at: datetime


class BudgetProgress(BaseModel):
    budget: BudgetResponse
    category_name: str
    period_end: date
    spent: Decimal
    remaining: Decimal
    utilization_percent: Decimal
    status: Literal["on_track", "warning", "exceeded"]


class BudgetListResponse(BaseModel):
    items: list[BudgetProgress]
    total: int
