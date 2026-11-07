"""create monthly category budgets

Revision ID: a91d3c7e4b20
Revises: 8c2f4a91d6e0
Create Date: 2026-11-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a91d3c7e4b20"
down_revision: Union[str, Sequence[str], None] = "8c2f4a91d6e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "budgets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(19, 4), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("alert_threshold", sa.Integer(), server_default="80", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_budgets_amount_positive"),
        sa.CheckConstraint("alert_threshold >= 1 AND alert_threshold <= 100", name="ck_budgets_alert_threshold_range"),
        sa.CheckConstraint("char_length(currency) = 3", name="ck_budgets_currency_length"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "category_id", "period_start", "currency", name="uq_budgets_user_category_period_currency"),
    )
    op.create_index("ix_budgets_user_period", "budgets", ["user_id", "period_start"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_budgets_user_period", table_name="budgets")
    op.drop_table("budgets")
