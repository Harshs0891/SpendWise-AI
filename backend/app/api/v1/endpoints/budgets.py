from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.budget import (
    BudgetCreate,
    BudgetListResponse,
    BudgetProgress,
    BudgetUpdate,
)
from app.services.budget_service import (
    create_budget,
    delete_budget,
    get_budget,
    list_budgets,
    update_budget,
)

# All routes in this router are mounted under /api/v1/budgets.
router = APIRouter()


@router.post(
    "",
    response_model=BudgetProgress,
    status_code=status.HTTP_201_CREATED,
)
def create_budget_endpoint(
    data: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a monthly budget for the authenticated user.

    Example:
        POST /api/v1/budgets
        {
            "category_id": "<expense-category-uuid>",
            "amount": "10000.00",
            "currency": "INR",
            "period_start": "2026-11-01",
            "alert_threshold": 80
        }
    """
    try:
        return create_budget(db, current_user.id, data)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get(
    "",
    response_model=BudgetListResponse,
)
def list_budgets_endpoint(
    # Example: 2026-11-01 filters the list to November 2026.
    period_start: date | None = Query(
        default=None,
        description="First day of the target month, e.g. 2026-11-01",
    ),
    # Example: INR filters the list to Indian Rupee budgets.
    currency: str | None = Query(
        default=None,
        min_length=3,
        max_length=3,
        pattern=r"^[A-Za-z]{3}$",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List the authenticated user's budgets with live spending progress."""
    try:
        items = list_budgets(db, current_user.id, period_start, currency)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return {"items": items, "total": len(items)}


@router.get(
    "/{budget_id}",
    response_model=BudgetProgress,
)
def get_budget_endpoint(
    budget_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve one owned budget and its current spending progress."""
    budget = get_budget(db, current_user.id, budget_id)

    if budget is None:
        raise HTTPException(status_code=404, detail="Budget not found.")

    return budget


@router.patch(
    "/{budget_id}",
    response_model=BudgetProgress,
)
def update_budget_endpoint(
    budget_id: UUID,
    data: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Partially update a budget.

    Example body:
        {"amount": "12000.00"}
    """
    try:
        budget = update_budget(db, current_user.id, budget_id, data)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    if budget is None:
        raise HTTPException(status_code=404, detail="Budget not found.")

    return budget


@router.delete(
    "/{budget_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_budget_endpoint(
    budget_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a budget owned by the authenticated user."""
    if not delete_budget(db, current_user.id, budget_id):
        raise HTTPException(status_code=404, detail="Budget not found.")

    return Response(status_code=status.HTTP_204_NO_CONTENT)
