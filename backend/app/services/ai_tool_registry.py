
"""
Registry of approved read-only tools available to Gemini.

Gemini can request these tools, but it cannot execute them.
The backend validates arguments and executes only functions
registered in this module.

The authenticated user ID is injected by the backend and
is never accepted as a model-generated argument.
"""

from datetime import date
from typing import Any
from uuid import UUID

from google.genai import types
from sqlalchemy.orm import Session

from app.services import ai_finance_tools


# Gemini receives these declarations, not direct Python functions.
FINANCE_TOOL_DECLARATIONS = [
    {
        "name": "get_financial_overview",
        "description": (
            "Get the user's total income, expenses, and net savings. "
            "Results are grouped by currency. Use this for overall "
            "financial summaries."
        ),
        "parameters_json_schema": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Optional start date in YYYY-MM-DD format.",
                },
                "end_date": {
                    "type": "string",
                    "description": "Optional end date in YYYY-MM-DD format.",
                },
                "currency": {
                    "type": "string",
                    "description": "Optional three-letter currency code, e.g. INR.",
                },
            },
        },
    },
    {
        "name": "get_spending_by_category",
        "description": (
            "Get expense totals grouped by category, including "
            "percentages. Use this to answer category spending questions."
        ),
        "parameters_json_schema": {
            "type": "object",
            "properties": {
                "currency": {
                    "type": "string",
                    "description": "Three-letter currency code, e.g. INR.",
                },
                "start_date": {
                    "type": "string",
                    "description": "Optional start date in YYYY-MM-DD format.",
                },
                "end_date": {
                    "type": "string",
                    "description": "Optional end date in YYYY-MM-DD format.",
                },
            },
            "required": ["currency"],
        },
    },
    {
        "name": "get_monthly_cash_flow",
        "description": (
            "Get monthly income and expense totals for one currency. "
            "Use this to analyze cash flow over time."
        ),
        "parameters_json_schema": {
            "type": "object",
            "properties": {
                "currency": {
                    "type": "string",
                    "description": "Three-letter currency code, e.g. INR.",
                },
                "start_date": {
                    "type": "string",
                    "description": "Optional start date in YYYY-MM-DD format.",
                },
                "end_date": {
                    "type": "string",
                    "description": "Optional end date in YYYY-MM-DD format.",
                },
            },
            "required": ["currency"],
        },
    },
    {
        "name": "get_budget_status",
        "description": (
            "Get the user's budgets, spending progress, remaining amounts, "
            "and budget status. Optionally filter by month and currency."
        ),
        "parameters_json_schema": {
            "type": "object",
            "properties": {
                "period_start": {
                    "type": "string",
                    "description": (
                        "Optional first day of a month in YYYY-MM-DD format."
                    ),
                },
                "currency": {
                    "type": "string",
                    "description": "Optional three-letter currency code.",
                },
            },
        },
    },
    {
        "name": "get_recent_transactions",
        "description": "Get the user's most recent income and expense transactions.",
        "parameters_json_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of transactions to return, from 1 to 20.",
                },
            },
        },
    },
    {
        "name": "get_account_balances",
        "description": "Get the calculated balances of the user's active accounts.",
        "parameters_json_schema": {
            "type": "object",
            "properties": {},
        },
    },
]


FINANCE_TOOL = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(**declaration)
        for declaration in FINANCE_TOOL_DECLARATIONS
    ]
)


def _parse_optional_date(value: Any, field_name: str) -> date | None:
    """Validate and parse a model-provided ISO date."""

    if value is None:
        return None

    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a YYYY-MM-DD string.")

    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(
            f"{field_name} must be a valid YYYY-MM-DD date."
        ) from None


def _validate_currency(value: Any) -> str:
    """Validate a three-letter currency code."""

    if not isinstance(value, str):
        raise ValueError("currency must be a string.")

    currency = value.strip().upper()

    if len(currency) != 3 or not currency.isalpha():
        raise ValueError("currency must be a three-letter code.")

    return currency


def execute_finance_tool(
    *,
    tool_name: str,
    arguments: dict[str, Any],
    db: Session,
    user_id: UUID,
) -> dict:
    """
    Execute one approved finance tool.

    Security controls:
    - Unknown tools are rejected.
    - Unknown arguments are rejected.
    - user_id comes exclusively from backend authentication.
    - Tool functions remain read-only.
    """

    if not isinstance(arguments, dict):
        raise ValueError("Tool arguments must be an object.")

    if tool_name == "get_financial_overview":
        allowed = {"start_date", "end_date", "currency"}

        if set(arguments) - allowed:
            raise ValueError("Unsupported financial overview arguments.")

        start_date = _parse_optional_date(
            arguments.get("start_date"), "start_date"
        )
        end_date = _parse_optional_date(
            arguments.get("end_date"), "end_date"
        )

        if start_date and end_date and start_date > end_date:
            raise ValueError("start_date cannot be later than end_date.")

        currency = arguments.get("currency")
        if currency is not None:
            currency = _validate_currency(currency)

        return ai_finance_tools.get_financial_overview(
            db=db,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            currency=currency,
        )

    if tool_name == "get_spending_by_category":
        allowed = {"currency", "start_date", "end_date"}

        if set(arguments) - allowed:
            raise ValueError("Unsupported category spending arguments.")

        currency = _validate_currency(arguments.get("currency"))
        start_date = _parse_optional_date(
            arguments.get("start_date"), "start_date"
        )
        end_date = _parse_optional_date(
            arguments.get("end_date"), "end_date"
        )

        if start_date and end_date and start_date > end_date:
            raise ValueError("start_date cannot be later than end_date.")

        return ai_finance_tools.get_spending_by_category(
            db=db,
            user_id=user_id,
            currency=currency,
            start_date=start_date,
            end_date=end_date,
        )

    if tool_name == "get_monthly_cash_flow":
        allowed = {"currency", "start_date", "end_date"}

        if set(arguments) - allowed:
            raise ValueError("Unsupported cash flow arguments.")

        currency = _validate_currency(arguments.get("currency"))
        start_date = _parse_optional_date(
            arguments.get("start_date"), "start_date"
        )
        end_date = _parse_optional_date(
            arguments.get("end_date"), "end_date"
        )

        if start_date and end_date and start_date > end_date:
            raise ValueError("start_date cannot be later than end_date.")

        return ai_finance_tools.get_monthly_cash_flow(
            db=db,
            user_id=user_id,
            currency=currency,
            start_date=start_date,
            end_date=end_date,
        )

    if tool_name == "get_budget_status":
        allowed = {"period_start", "currency"}

        if set(arguments) - allowed:
            raise ValueError("Unsupported budget status arguments.")

        period_start = _parse_optional_date(
            arguments.get("period_start"), "period_start"
        )

        if period_start and period_start.day != 1:
            raise ValueError("period_start must be the first day of a month.")

        currency = arguments.get("currency")
        if currency is not None:
            currency = _validate_currency(currency)

        return ai_finance_tools.get_budget_status(
            db=db,
            user_id=user_id,
            period_start=period_start,
            currency=currency,
        )

    if tool_name == "get_recent_transactions":
        if set(arguments) - {"limit"}:
            raise ValueError("Unsupported recent transaction arguments.")

        limit = arguments.get("limit", 10)

        if isinstance(limit, bool) or not isinstance(limit, int):
            raise ValueError("limit must be an integer.")

        if not 1 <= limit <= 20:
            raise ValueError("limit must be between 1 and 20.")

        return ai_finance_tools.get_recent_transactions(
            db=db,
            user_id=user_id,
            limit=limit,
        )

    if tool_name == "get_account_balances":
        if arguments:
            raise ValueError("This tool does not accept arguments.")

        return ai_finance_tools.get_account_balances(
            db=db,
            user_id=user_id,
        )

    raise ValueError(f"Unknown finance tool: {tool_name}")
