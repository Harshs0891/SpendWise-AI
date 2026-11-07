from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.analytics import (
    AnalyticsSummaryResponse,
    CashFlowResponse,
    CategoryBreakdownResponse,
    RecentTransactionsResponse,
    AccountBalancesResponse,
)
from app.services.analytics_service import (
    get_dashboard_summary,
    get_monthly_cash_flow,
    get_category_breakdown,
    get_recent_transactions,
    get_account_balances,
)

router = APIRouter()


def validate_date_range(
    start_date: date | None,
    end_date: date | None,
):
    """Ensure the start date is not later than the end date."""
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=422,
            detail="start_date cannot be later than end_date",
        )


# 1. Dashboard summary
@router.get(
    "/summary",
    response_model=AnalyticsSummaryResponse,
)
def dashboard_summary(
    start_date: date | None = None,
    end_date: date | None = None,
    currency: str | None = Query(default=None, min_length=3, max_length=3),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return income, expenses, and net savings grouped by currency."""
    validate_date_range(start_date, end_date)

    return get_dashboard_summary(
        db=db,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        currency=currency,
    )


# 2. Monthly cash flow
@router.get(
    "/cash-flow",
    response_model=CashFlowResponse,
)
def monthly_cash_flow(
    currency: str = Query(..., min_length=3, max_length=3),
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return monthly income and expenses for the selected currency."""
    validate_date_range(start_date, end_date)

    return get_monthly_cash_flow(
        db=db,
        user_id=current_user.id,
        currency=currency,
        start_date=start_date,
        end_date=end_date,
    )


# 3. Category-wise spending
@router.get(
    "/category-breakdown",
    response_model=CategoryBreakdownResponse,
)
def category_breakdown(
    currency: str = Query(..., min_length=3, max_length=3),
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return expense distribution across categories."""
    validate_date_range(start_date, end_date)

    return get_category_breakdown(
        db=db,
        user_id=current_user.id,
        currency=currency,
        start_date=start_date,
        end_date=end_date,
    )


# 4. Recent transactions
@router.get(
    "/recent-transactions",
    response_model=RecentTransactionsResponse,
)
def recent_transactions(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the latest transactions for the authenticated user."""
    return get_recent_transactions(
        db=db,
        user_id=current_user.id,
        limit=limit,
    )


# 5. Account balances
@router.get(
    "/account-balances",
    response_model=AccountBalancesResponse,
)
def account_balances(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return calculated balances for the user's active accounts."""
    return get_account_balances(
        db=db,
        user_id=current_user.id,
    )