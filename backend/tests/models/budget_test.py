from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.models.budget import Budget


def test_budget_model_declares_unique_monthly_budget_constraint():
    constraints = {c.name for c in Budget.__table__.constraints}

    assert "uq_budgets_user_category_period_currency" in constraints
    assert "ck_budgets_amount_positive" in constraints
    assert "ck_budgets_alert_threshold_range" in constraints


def test_budget_model_stores_decimal_amount_and_month_start():
    budget = Budget(
        id=uuid4(), user_id=uuid4(), category_id=uuid4(),
        amount=Decimal("10000.2500"), currency="INR",
        period_start=date(2026, 11, 1), alert_threshold=80,
    )

    assert budget.amount == Decimal("10000.2500")
    assert budget.period_start == date(2026, 11, 1)
    assert budget.alert_threshold == 80
