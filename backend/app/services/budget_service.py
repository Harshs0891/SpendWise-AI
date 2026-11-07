import calendar
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Budget, Category, Transaction
from app.schemas.budget import BudgetCreate, BudgetUpdate


def _period_end(period_start: date) -> date:
    """
    Return the final calendar day for a budget month.

    Example:
        _period_end(date(2026, 11, 1)) -> date(2026, 11, 30)
        _period_end(date(2026, 2, 1))  -> date(2026, 2, 28)

    calendar.monthrange handles different month lengths and leap years.
    """
    return date(
        period_start.year,
        period_start.month,
        calendar.monthrange(period_start.year, period_start.month)[1],
    )


def _validate_expense_category(
    db: Session,
    user_id: UUID,
    category_id: UUID,
) -> Category:
    """
    Ensure the requested category is an expense category visible to the user.

    A valid category is either:
        1. A shared system expense category.
        2. A custom expense category owned by this user.

    Income categories and another user's private categories are rejected.
    """
    category = db.scalar(
        select(Category).where(
            Category.id == category_id,
            Category.kind == "expense",
            (Category.user_id == user_id) | (Category.is_system.is_(True)),
        )
    )

    if category is None:
        raise ValueError("Expense category not found or not accessible.")

    return category


def _to_progress(db: Session, budget: Budget) -> dict:
    """
    Calculate live spending progress for one budget.

    Example:
        Budget: INR 10,000 for Food in November 2026.
        Matching expenses: INR 3,000 + INR 5,000.
        spent = 8,000; remaining = 2,000; utilization = 80%.
        With alert_threshold=80, status becomes "warning".

    Only transactions matching the budget owner, category, currency,
    and calendar month are counted. Transfer ledger entries are excluded.
    """
    # Resolve the category name for a readable API response.
    category = db.get(Category, budget.category_id)

    # Determine the inclusive end date for the budget month.
    end_date = _period_end(budget.period_start)

    # Sum only ordinary expense transactions matching this budget.
    # The currency condition prevents INR and USD from being combined.
    # transfer_id IS NULL excludes the debit/credit legs of transfers.
    spent = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == budget.user_id,
            Transaction.category_id == budget.category_id,
            Transaction.type == "expense",
            Transaction.currency == budget.currency,
            Transaction.transfer_id.is_(None),
            Transaction.transaction_date >= budget.period_start,
            Transaction.transaction_date <= end_date,
        )
    ) or Decimal("0.0000")

    # Remaining can be negative when the user exceeds the budget.
    remaining = budget.amount - spent

    # Decimal arithmetic avoids floating-point rounding in percentages.
    utilization = (
        spent / budget.amount * Decimal("100")
    ).quantize(Decimal("0.01"))

    # Exceeded takes priority over warning at or above 100%.
    if spent >= budget.amount:
        state = "exceeded"
    elif utilization >= budget.alert_threshold:
        state = "warning"
    else:
        state = "on_track"

    return {
        "budget": budget,
        "category_name": category.name if category else "Unknown",
        "period_end": end_date,
        "spent": spent,
        "remaining": remaining,
        "utilization_percent": utilization,
        "status": state,
    }


def create_budget(db: Session, user_id: UUID, data: BudgetCreate) -> dict:
    """
    Create a monthly budget for the authenticated user.

    Example:
        data.amount = Decimal("10000.00")
        data.currency = "INR"
        data.period_start = date(2026, 11, 1)

    The service validates category ownership/type and prevents a second
    budget for the same user, category, month, and currency.
    """
    # Validate that the category is an accessible expense category.
    _validate_expense_category(db, user_id, data.category_id)

    # Check for an existing budget before attempting the insert.
    existing = db.scalar(
        select(Budget).where(
            Budget.user_id == user_id,
            Budget.category_id == data.category_id,
            Budget.period_start == data.period_start,
            Budget.currency == data.currency,
        )
    )

    if existing:
        raise ValueError(
            "A budget already exists for this category, month, and currency."
        )

    # Build the ORM object. user_id comes from authentication,
    # not from client-controlled request data.
    budget = Budget(
        user_id=user_id,
        category_id=data.category_id,
        amount=data.amount,
        currency=data.currency,
        period_start=data.period_start,
        alert_threshold=data.alert_threshold,
    )

    try:
        db.add(budget)
        db.commit()
        db.refresh(budget)
    except Exception:
        # Roll back the failed transaction before re-raising the error.
        db.rollback()
        raise

    # Return the newly created budget with its calculated progress.
    return _to_progress(db, budget)


def list_budgets(
    db: Session,
    user_id: UUID,
    period_start: date | None = None,
    currency: str | None = None,
) -> list[dict]:
    """
    List budgets owned by the authenticated user.

    Optional examples:
        period_start=date(2026, 11, 1) -> only November 2026 budgets
        currency="INR"                 -> only INR budgets

    Every result includes its live spending progress.
    """
    # Ownership filter is mandatory; users never see another user's budgets.
    statement = select(Budget).where(Budget.user_id == user_id)

    if period_start is not None:
        # Keep month filtering consistent with the stored first-of-month date.
        if period_start.day != 1:
            raise ValueError("period_start must be the first day of a month.")
        statement = statement.where(Budget.period_start == period_start)

    if currency is not None:
        statement = statement.where(Budget.currency == currency.upper())

    # Newer months appear first; creation time provides stable ordering.
    budgets = db.scalars(
        statement.order_by(Budget.period_start.desc(), Budget.created_at.desc())
    ).all()

    return [_to_progress(db, budget) for budget in budgets]


def get_budget(db: Session, user_id: UUID, budget_id: UUID) -> dict | None:
    """
    Retrieve one budget only when it belongs to the authenticated user.

    Returns None for both a missing budget and another user's budget,
    avoiding disclosure of whether another user's resource exists.
    """
    budget = db.scalar(
        select(Budget).where(
            Budget.id == budget_id,
            Budget.user_id == user_id,
        )
    )

    return _to_progress(db, budget) if budget else None


def update_budget(
    db: Session,
    user_id: UUID,
    budget_id: UUID,
    data: BudgetUpdate,
) -> dict | None:
    """
    Partially update an owned budget.

    Example:
        {"amount": "12000.00"} updates only the amount.
        {"alert_threshold": 90} updates only the warning threshold.

    The category, currency, and month are immutable after creation.
    """
    # Restrict lookup to the authenticated user's own budget.
    budget = db.scalar(
        select(Budget).where(
            Budget.id == budget_id,
            Budget.user_id == user_id,
        )
    )

    if budget is None:
        return None

    # exclude_unset=True preserves every field omitted from the PATCH body.
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(budget, field, value)

    try:
        db.commit()
        db.refresh(budget)
    except Exception:
        db.rollback()
        raise

    return _to_progress(db, budget)


def delete_budget(db: Session, user_id: UUID, budget_id: UUID) -> bool:
    """
    Delete one budget owned by the authenticated user.

    Returns:
        True  -> the budget was found and deleted.
        False -> no matching owned budget exists.

    Deleting a budget does not delete its category or transactions.
    """
    budget = db.scalar(
        select(Budget).where(
            Budget.id == budget_id,
            Budget.user_id == user_id,
        )
    )

    if budget is None:
        return False

    try:
        db.delete(budget)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return True
