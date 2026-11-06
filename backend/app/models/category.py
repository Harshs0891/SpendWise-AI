
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Category(Base):
    """
    Represents an income or expense category.

    Categories can be:
    1. System categories: shared across all users (user_id is NULL).
    2. Custom categories: created and owned by an individual user.
    """

    __tablename__ = "categories"

    __table_args__ = (
        # A category can only represent income or expense.
        CheckConstraint(
            "kind IN ('income', 'expense')",
            name="ck_categories_kind",
        ),

        # Helps retrieve categories belonging to a user,
        # optionally filtered by category kind.
        Index(
            "ix_categories_user_id_kind",
            "user_id",
            "kind",
        ),
    )

    # Unique identifier for every category.
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # NULL means this is a shared system category.
    # Otherwise, it belongs to a specific user.
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Example: Food, Rent, Salary, Shopping.
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # Only "income" or "expense".
    kind: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # Optional icon identifier for frontend display.
    icon: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # Optional hex color for frontend display.
    color: Mapped[str | None] = mapped_column(
        String(7),
        nullable=True,
    )

    # System categories are shared and should not be modified
    # or deleted by regular users.
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )

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
