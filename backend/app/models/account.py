
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Account(Base):
    """
    SQLAlchemy model representing a financial account owned by a user.

    Examples:
        - HDFC Savings (bank)
        - Personal Wallet (wallet)
        - Cash (cash)
        - Emergency Fund (savings)
        - ICICI Credit Card (credit_card)

    Each account belongs to exactly one user.
    """

    __tablename__ = "accounts"

    # Database-level constraints protect our data even if someone
    # bypasses the Pydantic schemas or application services.
    __table_args__ = (
        # Only allow supported account types.
        CheckConstraint(
            "account_type IN ('cash', 'bank', 'savings', 'wallet', 'credit_card')",
            name="ck_accounts_account_type",
        ),

        # Currency must contain exactly three characters.
        # Example: INR, USD, EUR.
        CheckConstraint(
            "char_length(currency) = 3",
            name="ck_accounts_currency_length",
        ),

        # Efficiently retrieve a user's active accounts.
        Index(
            "ix_accounts_user_id_is_active",
            "user_id",
            "is_active",
        ),
    )

    # Unique identifier for an account.
    # uuid.uuid4 generates a new UUID when an account is created.
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # The user who owns this account.
    #
    # ForeignKey ensures that an account cannot reference a
    # non-existent user.
    #
    # index=True helps when retrieving accounts belonging to a user.
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # User-friendly account name.
    # Example: "HDFC Savings Account".
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # Account classification.
    # Examples: cash, bank, savings, wallet, credit_card.
    account_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # ISO 4217 currency code.
    # Examples: INR, USD, EUR.
    #
    # We store the currency explicitly because an amount without
    # a currency is financially ambiguous.
    currency: Mapped[str] = mapped_column(
        String(3),
        default="INR",
        server_default="INR",
        nullable=False,
    )

    # The balance present when the account is first added.
    #
    # Numeric(19, 4) supports exact decimal storage.
    # Never use Float for financial amounts.
    #
    # Decimal("0.0000") avoids introducing binary floating-point
    # precision errors.
    opening_balance: Mapped[Decimal] = mapped_column(
        Numeric(19, 4),
        default=Decimal("0.0000"),
        server_default="0",
        nullable=False,
    )

    # Soft deactivation instead of deleting an account.
    #
    # Example:
    # If a user closes a bank account, we set is_active=False.
    # Historical transactions can still refer to that account.
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )

    # Timestamp when the account is created.
    # The database generates the timestamp.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Timestamp updated whenever SQLAlchemy updates this ORM object.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
