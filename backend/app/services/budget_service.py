import calendar
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Budget, Category, Transaction
from app.schemas.budget import BudgetCreate, BudgetUpdate


def _period_end(period_start: date) -> date:
    return date(
        period_start.year,
        period_start.month,
        calendar.monthrange(period_start.year, period_start.month)[1],
    )


def _validate_expense_category(db: Session, user_id: UUID, category_id: UUID) -> Category:
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
    category = db.get(Category, budget.category_id)
    end_date = _period_end(budget.period_start)
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

    remaining = budget.amount - spent
    utilization = (spent / budget.amount * Decimal("100")).quantize(Decimal("0.01"))
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
    _validate_expense_category(db, user_id, data.category_id)
    existing = db.scalar(
        select(Budget).where(
            Budget.user_id == user_id,
            Budget.category_id == data.category_id,
            Budget.period_start == data.period_start,
            Budget.currency == data.currency,
        )
    )
    if existing:
        raise ValueError("A budget already exists for this category, month, and currency.")

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
        db.rollback()
        raise
    return _to_progress(db, budget)


def list_budgets(
    db: Session, user_id: UUID, period_start: date | None = None, currency: str | None = None
) -> list[dict]:
    statement = select(Budget).where(Budget.user_id == user_id)
    if period_start is not None:
        if period_start.day != 1:
            raise ValueError("period_start must be the first day of a month.")
        statement = statement.where(Budget.period_start == period_start)
    if currency is not None:
        statement = statement.where(Budget.currency == currency.upper())
    budgets = db.scalars(statement.order_by(Budget.period_start.desc(), Budget.created_at.desc())).all()
    return [_to_progress(db, budget) for budget in budgets]


def get_budget(db: Session, user_id: UUID, budget_id: UUID) -> dict | None:
    budget = db.scalar(
        select(Budget).where(Budget.id == budget_id, Budget.user_id == user_id)
    )
    return _to_progress(db, budget) if budget else None


def update_budget(
    db: Session, user_id: UUID, budget_id: UUID, data: BudgetUpdate
) -> dict | None:
    budget = db.scalar(
        select(Budget).where(Budget.id == budget_id, Budget.user_id == user_id)
    )
    if budget is None:
        return None
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
    budget = db.scalar(
        select(Budget).where(Budget.id == budget_id, Budget.user_id == user_id)
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
