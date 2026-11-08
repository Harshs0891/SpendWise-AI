
"""
Deterministic financial insights for SpendWise AI.

All financial calculations happen in Python using existing analytics
services. Gemini can later interpret these results, but must never
calculate or invent the underlying financial figures.
"""

import calendar
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.services.analytics_service import (
    get_dashboard_summary,
    get_category_breakdown,
)


def _get_month_range(reference_date: date) -> tuple[date, date]:
    """Return the first and last calendar dates of a month."""
    last_day = calendar.monthrange(
        reference_date.year,
        reference_date.month,
    )[1]

    return (
        date(reference_date.year, reference_date.month, 1),
        date(reference_date.year, reference_date.month, last_day),
    )


def _get_previous_month(reference_date: date) -> date:
    """Return the first day of the previous calendar month."""
    if reference_date.month == 1:
        return date(reference_date.year - 1, 12, 1)

    return date(reference_date.year, reference_date.month - 1, 1)


def _percentage_change(
    current: Decimal,
    previous: Decimal,
) -> Decimal | None:
    """
    Calculate percentage change.

    Return None when the previous value is zero because percentage
    growth from zero is mathematically undefined.
    """
    if previous == 0:
        return None

    return (
        (current - previous) / previous * Decimal("100")
    ).quantize(Decimal("0.01"))


def _build_currency_insight(
    db: Session,
    user_id: UUID,
    currency: str,
    start_date: date,
    end_date: date,
    previous_start: date,
    previous_end: date,
) -> dict:
    """Build spending insights for one currency."""

    # Current-month financial summary.
    current_summary = get_dashboard_summary(
        db=db,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        currency=currency,
    )

    # Previous-month financial summary.
    previous_summary = get_dashboard_summary(
        db=db,
        user_id=user_id,
        start_date=previous_start,
        end_date=previous_end,
        currency=currency,
    )

    current = (
        current_summary.items[0]
        if current_summary.items
        else None
    )

    previous = (
        previous_summary.items[0]
        if previous_summary.items
        else None
    )

    zero = Decimal("0.00")

    income = current.total_income if current else zero
    expenses = current.total_expenses if current else zero
    savings = current.net_savings if current else zero

    previous_expenses = (
        previous.total_expenses if previous else zero
    )

    previous_income = (
        previous.total_income if previous else zero
    )

    # Calculate savings rate only when income is positive.
    savings_rate = (
        (savings / income) * Decimal("100")
    ).quantize(Decimal("0.01")) if income > 0 else None

    # Retrieve category-level spending for both periods.
    current_categories = get_category_breakdown(
        db=db,
        user_id=user_id,
        currency=currency,
        start_date=start_date,
        end_date=end_date,
    )

    previous_categories = get_category_breakdown(
        db=db,
        user_id=user_id,
        currency=currency,
        start_date=previous_start,
        end_date=previous_end,
    )

    category_items = current_categories.items

    # Identify the highest-spending category.
    top_category = (
        max(category_items, key=lambda item: item.total)
        if category_items
        else None
    )

    previous_category_map = {
        item.category_name: item.total
        for item in previous_categories.items
    }

    category_insights = []

    for item in category_items:
        previous_amount = previous_category_map.get(
            item.category_name,
            zero,
        )

        category_insights.append({
            "category": item.category_name,
            "amount": str(item.total),
            "percentage_of_spending": str(item.percentage),
            "previous_month_amount": str(previous_amount),
            "percentage_change": (
                str(_percentage_change(item.total, previous_amount))
                if previous_amount != 0
                else None
            ),
        })

    observations = []

    if income > 0 and savings < 0:
        observations.append(
            "Expenses exceeded income during this period."
        )

    if top_category and top_category.percentage >= 40:
        observations.append(
            f"{top_category.category_name} accounts for "
            f"{top_category.percentage}% of your expenses."
        )

    expense_change = _percentage_change(
        expenses,
        previous_expenses,
    )

    if expense_change is not None:
        if expense_change > 0:
            observations.append(
                f"Expenses increased by {expense_change}% "
                "compared with the previous month."
            )
        elif expense_change < 0:
            observations.append(
                f"Expenses decreased by {abs(expense_change)}% "
                "compared with the previous month."
            )

    return {
        "currency": currency,
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
        "financial_summary": {
            "total_income": str(income),
            "total_expenses": str(expenses),
            "net_savings": str(savings),
            "savings_rate": (
                str(savings_rate)
                if savings_rate is not None
                else None
            ),
        },
        "comparison": {
            "previous_month_income": str(previous_income),
            "previous_month_expenses": str(previous_expenses),
            "expense_change_percentage": (
                str(expense_change)
                if expense_change is not None
                else None
            ),
        },
        "top_category": (
            {
                "name": top_category.category_name,
                "amount": str(top_category.total),
                "percentage": str(top_category.percentage),
            }
            if top_category
            else None
        ),
        "categories": category_insights,
        "observations": observations,
    }


def get_spending_insights(
    db: Session,
    user_id: UUID,
    reference_date: date | None = None,
    currency: str | None = None,
) -> dict:
    """
    Generate deterministic spending insights for a user.

    Defaults to the current calendar month.

    If currency is omitted, results are returned separately for
    every currency found in the current month's transactions.
    """

    reference_date = reference_date or date.today()

    start_date, end_date = _get_month_range(reference_date)

    previous_start, previous_end = _get_month_range(
        _get_previous_month(reference_date)
    )

    # Determine which currencies have current-period activity.
    summary = get_dashboard_summary(
        db=db,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        currency=currency,
    )

    currencies = (
        [currency.upper()]
        if currency
        else [item.currency for item in summary.items]
    )

    insights = [
        _build_currency_insight(
            db=db,
            user_id=user_id,
            currency=selected_currency,
            start_date=start_date,
            end_date=end_date,
            previous_start=previous_start,
            previous_end=previous_end,
        )
        for selected_currency in currencies
    ]

    return {
        "generated_at": date.today().isoformat(),
        "insights": insights,
    }
