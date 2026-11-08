
"""
Monthly Financial Report service.

Combines deterministic spending insights and budget recommendations
into a single monthly financial report.
"""

import calendar
from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.services.ai_insights_service import get_spending_insights
from app.services.ai_budget_advisor import get_smart_budget_advice


def generate_monthly_report(
    db: Session,
    user_id: UUID,
    reference_date: date | None = None,
    currency: str | None = None,
) -> dict:
    """
    Generate a monthly report for the authenticated user.

    The report combines:
    - Income and expenses
    - Net savings and savings rate
    - Category-wise spending
    - Previous-month comparison
    - Budget health
    - Actionable observations
    """

    reference_date = reference_date or date.today()

    period_start = date(
        reference_date.year,
        reference_date.month,
        1,
    )

    last_day = calendar.monthrange(
        reference_date.year,
        reference_date.month,
    )[1]

    period_end = date(
        reference_date.year,
        reference_date.month,
        last_day,
    )

    # Generate spending insights using existing calculations.
    spending_data = get_spending_insights(
        db=db,
        user_id=user_id,
        reference_date=reference_date,
        currency=currency,
    )

    # Generate budget recommendations using existing budget logic.
    budget_data = get_smart_budget_advice(
        db=db,
        user_id=user_id,
        reference_date=reference_date,
        currency=currency,
    )

    # Create a separate report for each currency.
    currency_reports = []

    for insight in spending_data["insights"]:
        selected_currency = insight["currency"]

        # Keep budget figures in the same currency as the report.
        matching_budgets = [
            item
            for item in budget_data["recommendations"]
            if item["currency"] == selected_currency
        ]

        budget_summary = {
            "total_budgets": len(matching_budgets),
            "exceeded": sum(
                item["status"] == "exceeded"
                for item in matching_budgets
            ),
            "warning": sum(
                item["status"] == "warning"
                for item in matching_budgets
            ),
            "on_track": sum(
                item["status"] == "on_track"
                for item in matching_budgets
            ),
        }

        observations = list(insight["observations"])

        # Add budget-specific observations.
        if budget_summary["exceeded"]:
            observations.append(
                f"You have exceeded {budget_summary['exceeded']} "
                "of your budgets."
            )

        if budget_summary["warning"]:
            observations.append(
                f"{budget_summary['warning']} budgets are approaching "
                "their spending limits."
            )

        currency_reports.append({
            "currency": selected_currency,
            "financial_summary": insight["financial_summary"],
            "month_comparison": insight["comparison"],
            "top_category": insight["top_category"],
            "category_breakdown": insight["categories"],
            "budget_summary": budget_summary,
            "budget_recommendations": matching_budgets,
            "observations": observations,
        })

    return {
        "report_type": "monthly_financial_report",
        "period": {
            "start_date": period_start.isoformat(),
            "end_date": period_end.isoformat(),
            "month": period_start.strftime("%B"),
            "year": period_start.year,
        },
        "generated_at": date.today().isoformat(),
        "currency_reports": currency_reports,
    }
