from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

from app.schemas.account import AccountResponse
from app.schemas.budget import BudgetListResponse, BudgetProgress, BudgetResponse
from app.schemas.category import CategoryResponse
from app.schemas.transaction import TransactionListResponse, TransactionResponse
from app.schemas.transfer import TransferListResponse, TransferResponse
from app.schemas.user import UserResponse


def test_user_response_excludes_password_fields():
    now = datetime.now(timezone.utc)
    response = UserResponse(
        id=uuid4(), email="user@example.com", is_active=True,
        created_at=now, updated_at=now,
    )
    assert "password_hash" not in response.model_dump()
    assert "password" not in response.model_dump()


def test_category_response_supports_system_category():
    now = datetime.now(timezone.utc)
    response = CategoryResponse(
        id=uuid4(), user_id=None, name="Food", kind="expense",
        icon=None, color=None, is_system=True,
        created_at=now, updated_at=now,
    )
    assert response.is_system is True


def test_transaction_response_and_list_response():
    now = datetime.now(timezone.utc)
    item = TransactionResponse(
        id=uuid4(), user_id=uuid4(), account_id=uuid4(),
        category_id=None, type="expense", amount=Decimal("12.50"),
        currency="INR", description="Lunch", merchant=None,
        transaction_date=date(2026, 11, 7), notes=None,
        created_at=now, updated_at=now,
    )
    response = TransactionListResponse(items=[item], total=1, limit=20, offset=0)
    assert response.total == 1


def test_budget_response_progress_and_list_response():
    now = datetime.now(timezone.utc)
    budget = BudgetResponse(
        id=uuid4(), user_id=uuid4(), category_id=uuid4(),
        amount=Decimal("1000"), currency="INR",
        period_start=date(2026, 11, 1), alert_threshold=80,
        created_at=now, updated_at=now,
    )
    progress = BudgetProgress(
        budget=budget, category_name="Food",
        period_end=date(2026, 11, 30), spent=Decimal("800"),
        remaining=Decimal("200"), utilization_percent=Decimal("80.00"),
        status="warning",
    )
    response = BudgetListResponse(items=[progress], total=1)
    assert response.items[0].status == "warning"


def test_transfer_response_and_list_response():
    now = datetime.now(timezone.utc)
    item = TransferResponse(
        id=uuid4(), user_id=uuid4(), source_account_id=uuid4(),
        destination_account_id=uuid4(), amount=Decimal("100"),
        currency="INR", description="Transfer",
        transaction_date=date(2026, 11, 7), idempotency_key="key-1",
        created_at=now, debit_transaction_id=uuid4(),
        credit_transaction_id=uuid4(),
    )
    response = TransferListResponse(items=[item], total=1, limit=20, offset=0)
    assert response.items[0].idempotency_key == "key-1"


def test_account_response_is_constructible():
    now = datetime.now(timezone.utc)
    response = AccountResponse(
        id=uuid4(), user_id=uuid4(), name="Cash",
        account_type="cash", currency="INR",
        opening_balance=Decimal("0"), is_active=True,
        created_at=now, updated_at=now,
    )
    assert response.account_type == "cash"
