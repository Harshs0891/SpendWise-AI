
"""
Smart Budget Advisor for SpendWise AI.

Evaluates existing monthly budgets and generates deterministic,
read-only recommendations. No LLM or external API is required.
"""

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.services.budget_service import list_budgets


def _build_recommendation(budget_data: dict) -> dict:
    """Generate recommendations for one budget."""

    budget = budget_data["budget"]
    category = budget_data["category_name"]

    amount = Decimal(str(budget.amount))
    spent = Decimal(str(budget_data["spent"]))
    remaining = Decimal(str(budget_data["remaining"]))
    utilization = Decimal(str(budget_data["utilization_percent"]))

    status = budget_data["status"]

    if status == "exceeded":
        recommendation = (
            f"You have exceeded your {category} budget. "
            f"Review upcoming expenses and consider reducing "
            f"non-essential spending."
        )
        priority = "high"

    elif status == "warning":
        recommendation = (
            f"You have used {utilization}% of your {category} budget. "
            f"Only {remaining} {budget.currency} remains. "
            f"Monitor further spending in this category."
        )
        priority = "medium"

    else:
        recommendation = (
            f"Your {category} spending is within budget. "
            f"You have {remaining} {budget.currency} remaining."
        )
        priority = "low"

    return {
        "budget_id": str(budget.id),
        "category": category,
        "currency": budget.currency,
        "budget_amount": str(amount),
        "spent": str(spent),
        "remaining": str(remaining),
        "utilization_percent": str(utilization),
        "status": status,
        "priority": priority,
        "recommendation": recommendation,
    }


def get_smart_budget_advice(
    db: Session,
    user_id: UUID,
    reference_date: date | None = None,
    currency: str | None = None,
) -> dict:
    """
    Evaluate the authenticated user's budgets for a given month.

    The reference date can be any date within the target month.
    Budget records are never modified.
    """

    reference_date = reference_date or date.today()

    period_start = date(
        reference_date.year,
        reference_date.month,
        1,
    )

    budgets = list_budgets(
        db=db,
        user_id=user_id,
        period_start=period_start,
        currency=currency,
    )

    recommendations = [
        _build_recommendation(item)
        for item in budgets
    ]

    # Prioritize exceeded budgets, then warning budgets.
    priority_order = {
        "high": 0,
        "medium": 1,
        "low": 2,
    }

    recommendations.sort(
        key=lambda item: priority_order[item["priority"]]
    )

    total_budgets = len(recommendations)

    exceeded_count = sum(
        item["status"] == "exceeded"
        for item in recommendations
    )

    warning_count = sum(
        item["status"] == "warning"
        for item in recommendations
    )

    on_track_count = sum(
        item["status"] == "on_track"
        for item in recommendations
    )

    return {
        "period": period_start.isoformat(),
        "summary": {
            "total_budgets": total_budgets,
            "exceeded": exceeded_count,
            "warning": warning_count,
            "on_track": on_track_count,
        },
        "recommendations": recommendations,
    }
