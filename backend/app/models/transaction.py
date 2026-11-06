
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
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Transaction(Base):
    """
    Represents an income or expense entry in a user's financial ledger.

    Examples:
    - Income: Salary credited to a bank account.
    - Expense: Food purchase made using a wallet.

    Important:
    - Amounts are always positive.
    - The transaction type determines whether the amount
      increases or decreases the account balance.
    - Account balances will be calculated from the ledger.
    """

    __tablename__ = "transactions"

    __table_args__ = (
        # Only income and expense are supported initially.
        CheckConstraint(
            "type IN ('income', 'expense')",
            name="ck_transactions_type",
        ),

        # Transactions must have a positive amount.
        CheckConstraint(
            "amount > 0",
            name="ck_transactions_amount_positive",
        ),

        # Currency must contain exactly three characters.
        CheckConstraint(
            "char_length(currency) = 3",
            name="ck_transactions_currency_length",
        ),

        # Efficiently retrieve a user's transactions by date.
        Index(
            "ix_transactions_user_id_transaction_date",
            "user_id",
            "transaction_date",
        ),

        # Efficiently filter transactions by account.
        Index(
            "ix_transactions_user_id_account_id",
            "user_id",
            "account_id",
        ),

        # Efficiently filter transactions by category.
        Index(
            "ix_transactions_user_id_category_id",
            "user_id",
            "category_id",
        ),
    )

    # Unique identifier for every transaction.
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Identifies the user who owns this transaction.
    # Deleting the user deletes their transactions.
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Account affected by this transaction.
    # RESTRICT prevents physical deletion of an account
    # while transactions still reference it.
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Category is optional to support uncategorized entries.
    # If a category is physically deleted, the transaction
    # remains and its category_id becomes NULL.
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )

    # "income" or "expense".
    type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # Always store a positive amount.
    # Use Decimal instead of float to avoid financial
    # precision problems.
    amount: Mapped[Decimal] = mapped_column(
        Numeric(19, 4),
        nullable=False,
    )

    # ISO 4217 currency code, for example INR or USD.
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    # Short description of the transaction.
    # Example: Monthly salary or Grocery shopping.
    description: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Optional merchant or income source.
    # Example: Amazon, Swiggy, PayPal.
    merchant: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    # Calendar date on which the transaction occurred.
    # A Date is appropriate here because the user's
    # financial reporting is based on transaction dates.
    transaction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # Optional notes for additional details.
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Audit timestamps are timezone-aware.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
