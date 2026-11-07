import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Budget(Base):
    """
    SQLAlchemy model representing a monthly spending limit
    assigned by a user to one expense category.

    Example:
        A user creates a November 2026 Food budget:
            category_id = <Food category UUID>
            amount = Decimal("10000.00")
            currency = "INR"
            period_start = date(2026, 11, 1)
            alert_threshold = 80

        If the user spends INR 8,000 on Food during November,
        budget utilization becomes 80% and its status is "warning".

    Important:
        - A budget always belongs to one user.
        - Only expense categories can be budgeted.
        - One budget is allowed per user/category/month/currency.
        - Monetary values use Decimal/Numeric to avoid float errors.
        - period_start always stores the first day of the month.
    """

    __tablename__ = "budgets"

    __table_args__ = (
        # The budget amount must be positive.
        CheckConstraint(
            "amount > 0",
            name="ck_budgets_amount_positive",
        ),

        # Alert threshold is a percentage from 1 through 100.
        # Example: 80 means show a warning after spending reaches 80%.
        CheckConstraint(
            "alert_threshold >= 1 AND alert_threshold <= 100",
            name="ck_budgets_alert_threshold_range",
        ),

        # ISO 4217 currency codes contain exactly three characters.
        # Examples: INR, USD, EUR.
        CheckConstraint(
            "char_length(currency) = 3",
            name="ck_budgets_currency_length",
        ),

        # Prevent duplicate budgets for the same user, category,
        # month, and currency while allowing different currencies.
        UniqueConstraint(
            "user_id",
            "category_id",
            "period_start",
            "currency",
            name="uq_budgets_user_category_period_currency",
        ),

        # Speeds up queries such as "show this user's budgets
        # ordered by month".
        Index(
            "ix_budgets_user_period",
            "user_id",
            "period_start",
        ),
    )

    # Unique identifier generated for every budget.
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # User who owns this budget.
    # The API obtains this value from the authenticated user,
    # never from the request body.
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Expense category this budget tracks.
    # Example: Food, Shopping, Transport, or Rent.
    # The service verifies that the category is an expense
    # category visible to this user.
    category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Maximum planned spending for this category and month.
    # Numeric(19, 4) stores exact decimal values.
    # Example: Decimal("10000.00") represents INR 10,000.
    amount: Mapped[Decimal] = mapped_column(
        Numeric(19, 4),
        nullable=False,
    )

    # ISO 4217 currency code for the budget.
    # Spending in another currency is never added to this budget.
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    # First calendar day of the budget month.
    # Example: date(2026, 11, 1) represents November 2026.
    # The service calculates the last day of the month.
    period_start: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # Percentage at which the budget enters the warning state.
    # Example: 80 means warning at 80% utilization.
    # Defaults to 80 when the client does not provide a value.
    alert_threshold: Mapped[int] = mapped_column(
        default=80,
        server_default="80",
        nullable=False,
    )

    # Timestamp when the budget record was created.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Timestamp updated whenever the budget is modified.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
