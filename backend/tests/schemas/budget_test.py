from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.budget import BudgetCreate, BudgetUpdate


def test_budget_create_normalizes_currency_and_uses_threshold_default():
    budget = BudgetCreate(
        category_id=uuid4(), amount="1000.25",
        period_start=date(2026, 11, 1), currency=" inr ",
    )

    assert budget.currency == "INR"
    assert budget.alert_threshold == 80
    assert budget.amount == Decimal("1000.25")


@pytest.mark.parametrize("day", [2, 15, 31])
def test_budget_create_requires_first_day_of_month(day):
    with pytest.raises(ValidationError):
        BudgetCreate(
            category_id=uuid4(), amount="100",
            period_start=date(2026, 11, day),
        )


@pytest.mark.parametrize("threshold", [0, 101])
def test_budget_create_rejects_threshold_outside_range(threshold):
    with pytest.raises(ValidationError):
        BudgetCreate(
            category_id=uuid4(), amount="100",
            period_start=date(2026, 11, 1),
            alert_threshold=threshold,
        )


def test_budget_update_rejects_empty_and_explicit_null_updates():
    with pytest.raises(ValidationError):
        BudgetUpdate()
    with pytest.raises(ValidationError):
        BudgetUpdate(amount=None)


def test_budget_update_accepts_valid_partial_update():
    update = BudgetUpdate(alert_threshold=90)
    assert update.model_dump(exclude_unset=True) == {"alert_threshold": 90}
