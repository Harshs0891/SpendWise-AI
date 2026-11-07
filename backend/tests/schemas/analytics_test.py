from decimal import Decimal
from uuid import uuid4

from app.schemas.analytics import (
    AccountBalanceItem,
    AccountBalancesResponse,
    AnalyticsSummaryResponse,
    CashFlowResponse,
    CategoryBreakdownResponse,
    CategorySpending,
    CurrencySummary,
    MonthlyCashFlow,
    RecentTransactionItem,
    RecentTransactionsResponse,
)


def test_currency_summary_and_dashboard_response():
    summary = AnalyticsSummaryResponse(items=[
        CurrencySummary(
            currency="INR", total_income=Decimal("100"),
            total_expenses=Decimal("40"), net_savings=Decimal("60"),
        )
    ])

    assert summary.items[0].net_savings == Decimal("60")


def test_cash_flow_response_contains_monthly_items():
    response = CashFlowResponse(
        currency="INR",
        items=[MonthlyCashFlow(month="2026-11", income=Decimal("100"), expenses=Decimal("25"))],
    )

    assert response.items[0].month == "2026-11"


def test_category_breakdown_response_contains_category_totals():
    response = CategoryBreakdownResponse(
        currency="INR", total_expenses=Decimal("50"),
        items=[CategorySpending(
            category_id=None, category_name="Uncategorized",
            total=Decimal("50"), percentage=Decimal("100"),
        )],
    )

    assert response.items[0].percentage == Decimal("100")


def test_recent_transactions_response():
    from datetime import date

    item = RecentTransactionItem(
        id=uuid4(), type="expense", amount=Decimal("10"),
        currency="INR", description="Tea", merchant=None,
        transaction_date=date(2026, 11, 7), account_id=uuid4(),
        category_id=None, category_name=None,
    )
    response = RecentTransactionsResponse(items=[item], limit=10)

    assert response.items[0].description == "Tea"


def test_account_balances_response():
    item = AccountBalanceItem(
        account_id=uuid4(), account_name="Cash",
        account_type="cash", currency="INR",
        balance=Decimal("250"), balance_type="asset",
    )
    response = AccountBalancesResponse(items=[item])

    assert response.items[0].balance == Decimal("250")
