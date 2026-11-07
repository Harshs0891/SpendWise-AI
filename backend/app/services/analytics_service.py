from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models import Account, Category, Transaction
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


def get_dashboard_summary(
    db: Session,
    user_id: UUID,
    start_date: date | None = None,
    end_date: date | None = None,
    currency: str | None = None,
) -> AnalyticsSummaryResponse:
    """
    Calculate total income, expenses, and net savings.

    Financial totals are grouped by currency so that
    different currencies are never added together.

    Optional filters:
    - start_date: Include transactions from this date.
    - end_date: Include transactions up to this date.
    - currency: Include only the requested currency.
    """

    # -----------------------------------------------------
    # 1. Calculate income and expenses separately.
    # -----------------------------------------------------

    income_amount = case(
        (
            Transaction.type == "income",
            Transaction.amount,
        ),
        else_=Decimal("0.0000"),
    )

    expense_amount = case(
        (
            Transaction.type == "expense",
            Transaction.amount,
        ),
        else_=Decimal("0.0000"),
    )

    # -----------------------------------------------------
    # 2. Build the aggregation query.
    # -----------------------------------------------------

    statement = (
        select(
            Transaction.currency.label("currency"),
            func.coalesce(
                func.sum(income_amount),
                Decimal("0.0000"),
            ).label("total_income"),
            func.coalesce(
                func.sum(expense_amount),
                Decimal("0.0000"),
            ).label("total_expenses"),
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.transfer_id.is_(None),
        )
        .group_by(Transaction.currency)
        .order_by(Transaction.currency)
    )

    # -----------------------------------------------------
    # 3. Apply optional filters.
    # -----------------------------------------------------

    if start_date is not None:
        statement = statement.where(
            Transaction.transaction_date >= start_date
        )

    if end_date is not None:
        statement = statement.where(
            Transaction.transaction_date <= end_date
        )

    if currency is not None:
        statement = statement.where(
            Transaction.currency == currency.upper()
        )

    # -----------------------------------------------------
    # 4. Execute the query.
    # -----------------------------------------------------

    results = db.execute(statement).all()

    # -----------------------------------------------------
    # 5. Calculate net savings and build the response.
    # -----------------------------------------------------

    summary_items = []

    for row in results:
        total_income = row.total_income
        total_expenses = row.total_expenses

        # Net savings = Income - Expenses.
        net_savings = total_income - total_expenses

        summary_items.append(
            CurrencySummary(
                currency=row.currency,
                total_income=total_income,
                total_expenses=total_expenses,
                net_savings=net_savings,
            )
        )

    return AnalyticsSummaryResponse(
        items=summary_items
    )



def get_monthly_cash_flow(
    db: Session,
    user_id: UUID,
    currency: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> CashFlowResponse:
    """
    Calculate monthly income and expenses for one currency.

    Transactions are grouped by calendar month.

    A currency is required because a single cash-flow chart
    must never combine different currencies.
    """

    # -----------------------------------------------------
    # 1. Define conditional income and expense expressions.
    # -----------------------------------------------------

    income_amount = case(
        (
            Transaction.type == "income",
            Transaction.amount,
        ),
        else_=Decimal("0.0000"),
    )

    expense_amount = case(
        (
            Transaction.type == "expense",
            Transaction.amount,
        ),
        else_=Decimal("0.0000"),
    )

    # -----------------------------------------------------
    # 2. Extract the year and month from transaction_date.
    # -----------------------------------------------------

    # PostgreSQL converts dates into strings like 2026-11.
    month_expression = func.to_char(
        func.date_trunc("month", Transaction.transaction_date),
        "YYYY-MM",
    )

    # -----------------------------------------------------
    # 3. Build the monthly aggregation query.
    # -----------------------------------------------------

    statement = (
        select(
            month_expression.label("month"),
            func.sum(income_amount).label("income"),
            func.sum(expense_amount).label("expenses"),
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.transfer_id.is_(None),
            Transaction.currency == currency.upper(),
        )
        .group_by(month_expression)
        .order_by(month_expression)
    )

    # -----------------------------------------------------
    # 4. Apply optional date filters.
    # -----------------------------------------------------

    if start_date is not None:
        statement = statement.where(
            Transaction.transaction_date >= start_date
        )

    if end_date is not None:
        statement = statement.where(
            Transaction.transaction_date <= end_date
        )

    # -----------------------------------------------------
    # 5. Execute the query.
    # -----------------------------------------------------

    results = db.execute(statement).all()

    # -----------------------------------------------------
    # 6. Convert database results into response schemas.
    # -----------------------------------------------------

    monthly_items = [
        MonthlyCashFlow(
            month=row.month,
            income=row.income or Decimal("0.0000"),
            expenses=row.expenses or Decimal("0.0000"),
        )
        for row in results
    ]

    return CashFlowResponse(
        currency=currency.upper(),
        items=monthly_items,
    )


def get_category_breakdown(
    db: Session,
    user_id: UUID,
    currency: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> CategoryBreakdownResponse:
    """
    Calculate expense distribution across categories.

    Includes:
    - Shared system categories.
    - Categories owned by the authenticated user.
    - Uncategorized expenses.
    """

    statement = (
        select(
            Transaction.category_id,
            Category.name.label("category_name"),
            func.sum(Transaction.amount).label("total"),
        )
        .outerjoin(
            Category,
            Transaction.category_id == Category.id,
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.transfer_id.is_(None),
            Transaction.type == "expense",
            Transaction.currency == currency.upper(),
        )
        .group_by(
            Transaction.category_id,
            Category.name,
        )
        .order_by(
            func.sum(Transaction.amount).desc()
        )
    )

    if start_date is not None:
        statement = statement.where(
            Transaction.transaction_date >= start_date
        )

    if end_date is not None:
        statement = statement.where(
            Transaction.transaction_date <= end_date
        )

    results = db.execute(statement).all()

    total_expenses = sum(
        (row.total for row in results),
        Decimal("0.0000"),
    )

    category_items = []

    for row in results:
        category_total = row.total or Decimal("0.0000")

        percentage = (
            (category_total / total_expenses) * Decimal("100")
            if total_expenses > 0
            else Decimal("0.00")
        )

        category_items.append(
            CategorySpending(
                category_id=row.category_id,
                category_name=row.category_name or "Uncategorized",
                total=category_total,
                percentage=percentage.quantize(Decimal("0.01")),
            )
        )

    return CategoryBreakdownResponse(
        currency=currency.upper(),
        total_expenses=total_expenses,
        items=category_items,
    )


def get_recent_transactions(
    db: Session,
    user_id: UUID,
    limit: int = 10,
) -> RecentTransactionsResponse:
    """
    Fetch the most recent transactions for a user.

    Returns transaction details along with the category name.
    Results are ordered by transaction date and creation time.
    """

    statement = (
        select(
            Transaction.id,
            Transaction.type,
            Transaction.amount,
            Transaction.currency,
            Transaction.description,
            Transaction.merchant,
            Transaction.transaction_date,
            Transaction.account_id,
            Transaction.category_id,
            Category.name.label("category_name"),
        )
        .outerjoin(
            Category,
            Transaction.category_id == Category.id,
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.transfer_id.is_(None),
        )
        .order_by(
            Transaction.transaction_date.desc(),
            Transaction.created_at.desc(),
        )
        .limit(limit)
    )

    results = db.execute(statement).all()

    items = [
        RecentTransactionItem(
            id=row.id,
            type=row.type,
            amount=row.amount,
            currency=row.currency,
            description=row.description,
            merchant=row.merchant,
            transaction_date=row.transaction_date,
            account_id=row.account_id,
            category_id=row.category_id,
            category_name=row.category_name,
        )
        for row in results
    ]

    return RecentTransactionsResponse(
        items=items,
        limit=limit,
    )


def get_account_balances(
    db: Session,
    user_id: UUID,
) -> AccountBalancesResponse:
    """
    Calculate balances for all active accounts belonging to a user.

    Normal accounts:
        Opening balance + Income - Expenses

    Credit cards:
        Opening debt + Expenses - Payments/Income

    Credit card balances represent outstanding debt.
    """

    income_amount = case(
        (
            Transaction.type == "income",
            Transaction.amount,
        ),
        else_=Decimal("0.0000"),
    )

    expense_amount = case(
        (
            Transaction.type == "expense",
            Transaction.amount,
        ),
        else_=Decimal("0.0000"),
    )

    statement = (
        select(
            Account.id,
            Account.name,
            Account.account_type,
            Account.currency,
            Account.opening_balance,
            func.coalesce(
                func.sum(income_amount),
                Decimal("0.0000"),
            ).label("total_income"),
            func.coalesce(
                func.sum(expense_amount),
                Decimal("0.0000"),
            ).label("total_expenses"),
        )
        .outerjoin(
            Transaction,
            (
                (Account.id == Transaction.account_id)
                & (Transaction.user_id == user_id)
            ),
        )
        .where(
            Account.user_id == user_id,
            Account.is_active.is_(True),
        )
        .group_by(
            Account.id,
            Account.name,
            Account.account_type,
            Account.currency,
            Account.opening_balance,
        )
        .order_by(Account.name)
    )

    results = db.execute(statement).all()

    account_items = []

    for row in results:
        opening_balance = row.opening_balance or Decimal("0.0000")
        total_income = row.total_income or Decimal("0.0000")
        total_expenses = row.total_expenses or Decimal("0.0000")

        if row.account_type == "credit_card":
            balance = (
                opening_balance
                + total_expenses
                - total_income
            )
            balance_type = "debt"
        else:
            balance = (
                opening_balance
                + total_income
                - total_expenses
            )
            balance_type = "asset"

        account_items.append(
            AccountBalanceItem(
                account_id=row.id,
                account_name=row.name,
                account_type=row.account_type,
                currency=row.currency,
                balance=balance,
                balance_type=balance_type,
            )
        )

    return AccountBalancesResponse(
        items=account_items,
    )