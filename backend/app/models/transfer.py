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
    Uuid,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Transfer(Base):
    """
    Represents one money movement between two accounts owned by a user.

    The transfer is the aggregate root. Its two ledger entries are
    Transaction rows linked through Transaction.transfer_id.
    """

    __tablename__ = "transfers"

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_transfers_amount_positive"),
        CheckConstraint(
            "char_length(currency) = 3",
            name="ck_transfers_currency_length",
        ),
        CheckConstraint(
            "source_account_id <> destination_account_id",
            name="ck_transfers_distinct_accounts",
        ),
        UniqueConstraint(
            "user_id",
            "idempotency_key",
            name="uq_transfers_user_id_idempotency_key",
        ),
        Index("ix_transfers_user_id_transaction_date", "user_id", "transaction_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    source_account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=False,
    )

    destination_account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(19, 4),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    transaction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # Client-generated key makes retries safe after network timeouts.
    idempotency_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
