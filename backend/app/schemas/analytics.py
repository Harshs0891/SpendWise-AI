
from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# Supported account types.
AccountType = Literal[
    "cash",
    "bank",
    "savings",
    "wallet",
    "credit_card",
]


# ---------------------------------------------------------
# 1. Dashboard Summary
# ---------------------------------------------------------

class CurrencySummary(BaseModel):
    """Financial summary for a single currency."""

    currency: str
    total_income: Decimal
    total_expenses: Decimal
    net_savings: Decimal


class AnalyticsSummaryResponse(BaseModel):
    """Dashboard summary grouped by currency."""

    items: list[CurrencySummary]


# ---------------------------------------------------------
# 2. Cash Flow
# ---------------------------------------------------------

class MonthlyCashFlow(BaseModel):
    """Income and expenses for a particular month."""

    month: str  # Format: YYYY-MM
    income: Decimal
    expenses: Decimal


class CashFlowResponse(BaseModel):
    """Monthly cash-flow data for one currency."""

    currency: str
    items: list[MonthlyCashFlow]


# ---------------------------------------------------------
# 3. Category Breakdown
# ---------------------------------------------------------

class CategorySpending(BaseModel):
    """Spending information for an individual category."""

    category_id: UUID | None
    category_name: str
    total: Decimal
    percentage: Decimal


class CategoryBreakdownResponse(BaseModel):
    """Expense breakdown by category."""

    currency: str
    total_expenses: Decimal
    items: list[CategorySpending]


# ---------------------------------------------------------
# 4. Recent Transactions
# ---------------------------------------------------------

class RecentTransactionItem(BaseModel):
    """Transaction information for the dashboard."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: Literal["income", "expense"]
    amount: Decimal
    currency: str
    description: str
    merchant: str | None
    transaction_date: date
    account_id: UUID
    category_id: UUID | None
    category_name: str | None


class RecentTransactionsResponse(BaseModel):
    """Latest transactions for the authenticated user."""

    items: list[RecentTransactionItem]
    limit: int


# ---------------------------------------------------------
# 5. Account Balances
# ---------------------------------------------------------

class AccountBalanceItem(BaseModel):
    """Calculated balance for an individual account."""

    account_id: UUID
    account_name: str
    account_type: AccountType
    currency: str
    balance: Decimal
    balance_type: Literal["asset", "debt"]


class AccountBalancesResponse(BaseModel):
    """Calculated balances for the user's active accounts."""

    items: list[AccountBalanceItem]
