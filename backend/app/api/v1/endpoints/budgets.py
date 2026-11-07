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

router = APIRouter()


@router.post("", response_model=BudgetProgress, status_code=status.HTTP_201_CREATED)
def create_budget_endpoint(
    data: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return create_budget(db, current_user.id, data)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("", response_model=BudgetListResponse)
def list_budgets_endpoint(
    period_start: date | None = Query(default=None, description="First day of the target month, e.g. 2026-11-01"),
    currency: str | None = Query(default=None, min_length=3, max_length=3, pattern=r"^[A-Za-z]{3}$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        items = list_budgets(db, current_user.id, period_start, currency)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {"items": items, "total": len(items)}


@router.get("/{budget_id}", response_model=BudgetProgress)
def get_budget_endpoint(
    budget_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    budget = get_budget(db, current_user.id, budget_id)
    if budget is None:
        raise HTTPException(status_code=404, detail="Budget not found.")
    return budget


@router.patch("/{budget_id}", response_model=BudgetProgress)
def update_budget_endpoint(
    budget_id: UUID,
    data: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        budget = update_budget(db, current_user.id, budget_id, data)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if budget is None:
        raise HTTPException(status_code=404, detail="Budget not found.")
    return budget


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget_endpoint(
    budget_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not delete_budget(db, current_user.id, budget_id):
        raise HTTPException(status_code=404, detail="Budget not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
