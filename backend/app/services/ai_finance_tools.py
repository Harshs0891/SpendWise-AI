
"""
Controlled financial data tools for the SpendWise AI assistant.

These functions reuse existing financial services so that all
financial calculations remain deterministic and database-backed.

Security:
- user_id must come from the authenticated backend user.
- Never accept user_id from Gemini or an AI-generated tool argument.
- Every underlying query must remain scoped to that user.
"""

from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.schemas.budget import BudgetProgress
from app.services.analytics_service import (
    get_account_balances as analytics_account_balances,
    get_category_breakdown as analytics_category_breakdown,
    get_dashboard_summary,
    get_monthly_cash_flow as analytics_monthly_cash_flow,
    get_recent_transactions as analytics_recent_transactions,
)
from app.services.budget_service import list_budgets


def get_financial_overview(
    db: Session,
    user_id: UUID,
    start_date: date | None = None,
    end_date: date | None = None,
    currency: str | None = None,
) -> dict:
    """Return income, expenses, and net savings grouped by currency."""

    result = get_dashboard_summary(
        db=db,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        currency=currency,
    )

    return result.model_dump(mode="json")


def get_spending_by_category(
    db: Session,
    user_id: UUID,
    currency: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:
    """Return expense totals and percentages by category."""

    result = analytics_category_breakdown(
        db=db,
        user_id=user_id,
        currency=currency,
        start_date=start_date,
        end_date=end_date,
    )

    return result.model_dump(mode="json")


def get_monthly_cash_flow(
    db: Session,
    user_id: UUID,
    currency: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:
    """Return monthly income and expenses for one currency."""

    result = analytics_monthly_cash_flow(
        db=db,
        user_id=user_id,
        currency=currency,
        start_date=start_date,
        end_date=end_date,
    )

    return result.model_dump(mode="json")


def get_budget_status(
    db: Session,
    user_id: UUID,
    period_start: date | None = None,
    currency: str | None = None,
) -> dict:
    """Return the user's budgets with calculated spending progress."""

    budgets = list_budgets(
        db=db,
        user_id=user_id,
        period_start=period_start,
        currency=currency,
    )

    # Convert SQLAlchemy-backed budget data into JSON-safe
    # Pydantic responses before passing it to the AI layer.
    items = [
        BudgetProgress.model_validate(budget).model_dump(mode="json")
        for budget in budgets
    ]

    return {
        "items": items,
        "total": len(items),
    }


def get_recent_transactions(
    db: Session,
    user_id: UUID,
    limit: int = 10,
) -> dict:
    """Return recent transactions belonging to the user."""

    result = analytics_recent_transactions(
        db=db,
        user_id=user_id,
        limit=limit,
    )

    return result.model_dump(mode="json")


def get_account_balances(
    db: Session,
    user_id: UUID,
) -> dict:
    """Return calculated balances for the user's active accounts."""

    result = analytics_account_balances(
        db=db,
        user_id=user_id,
    )

    return result.model_dump(mode="json")
