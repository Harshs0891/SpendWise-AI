from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class BudgetCreate(BaseModel):
    """
    Validates the request body used to create a monthly budget.

    Example request:
        {
            "category_id": "b8f0f4d2-8a1d-4e7f-9d10-123456789abc",
            "amount": "10000.00",
            "currency": "INR",
            "period_start": "2026-11-01",
            "alert_threshold": 80
        }

    period_start must be the first day of the target month.
    The authenticated user ID is intentionally not accepted here;
    the endpoint supplies it from the access token.
    """

    # Category to which the budget applies.
    category_id: UUID

    # Planned spending limit. Decimal preserves financial precision.
    amount: Decimal = Field(
        gt=0,
        max_digits=19,
        decimal_places=4,
    )

    # Three-letter currency code. Defaults to INR.
    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
    )

    # First day of the budget month.
    # Example: 2026-11-01 represents the whole month of November.
    period_start: date

    # Percentage at which a warning should be raised.
    # Example: 80 means warn when 80% of the budget is used.
    alert_threshold: int = Field(
        default=80,
        ge=1,
        le=100,
    )

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        """Normalize user input, for example 'inr' to 'INR'."""
        return value.strip().upper() if isinstance(value, str) else value

    @field_validator("period_start")
    @classmethod
    def require_first_day_of_month(cls, value: date) -> date:
        """
        Keep one consistent representation for each calendar month.

        Valid:   2026-11-01
        Invalid: 2026-11-07
        """
        if value.day != 1:
            raise ValueError("period_start must be the first day of a month.")
        return value


class BudgetUpdate(BaseModel):
    """
    Validates a partial update to an existing budget.

    Example request:
        {
            "amount": "12000.00",
            "alert_threshold": 85
        }

    Only amount and alert_threshold are editable.
    Omitted fields retain their existing database values.
    """

    # New monthly spending limit, if the user wants to change it.
    amount: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=19,
        decimal_places=4,
    )

    # New warning threshold, if the user wants to change it.
    alert_threshold: int | None = Field(
        default=None,
        ge=1,
        le=100,
    )

    @model_validator(mode="after")
    def validate_changes(self):
        """
        Reject an empty update and explicit null values.

        {}                         -> invalid
        {"amount": null}           -> invalid
        {"alert_threshold": 90}    -> valid
        """
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")
        if "amount" in self.model_fields_set and self.amount is None:
            raise ValueError("amount cannot be null.")
        if "alert_threshold" in self.model_fields_set and self.alert_threshold is None:
            raise ValueError("alert_threshold cannot be null.")
        return self


class BudgetResponse(BaseModel):
    """
    Represents the persisted budget fields returned by the API.

    from_attributes=True allows Pydantic to read values directly
    from a SQLAlchemy Budget model instance.
    """

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
    """
    Represents a budget together with its calculated spending progress.

    Example:
        budget amount       = INR 10,000
        spent               = INR 8,000
        remaining           = INR 2,000
        utilization_percent = 80.00
        status              = "warning"

    Status values:
        on_track -> below the configured warning threshold
        warning  -> threshold reached, but budget not exhausted
        exceeded -> spending reached or exceeded the budget amount
    """

    budget: BudgetResponse
    category_name: str
    period_end: date
    spent: Decimal
    remaining: Decimal
    utilization_percent: Decimal
    status: Literal["on_track", "warning", "exceeded"]


class BudgetListResponse(BaseModel):
    """
    Paginated-style wrapper for the current budget list.

    Example:
        {
            "items": [ ... ],
            "total": 2
        }

    The current MVP returns all matching budgets; pagination
    can be introduced when the number of budgets requires it.
    """

    items: list[BudgetProgress]
    total: int
