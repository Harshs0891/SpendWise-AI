"""add atomic transfers and link ledger transactions

Revision ID: 8c2f4a91d6e0
Revises: 5bf5efb87ed4
Create Date: 2026-11-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8c2f4a91d6e0"
down_revision: Union[str, Sequence[str], None] = "5bf5efb87ed4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "transfers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("source_account_id", sa.Uuid(), nullable=False),
        sa.Column("destination_account_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=19, scale=4), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("amount > 0", name="ck_transfers_amount_positive"),
        sa.CheckConstraint(
            "char_length(currency) = 3",
            name="ck_transfers_currency_length",
        ),
        sa.CheckConstraint(
            "source_account_id <> destination_account_id",
            name="ck_transfers_distinct_accounts",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["source_account_id"], ["accounts.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["destination_account_id"], ["accounts.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "idempotency_key",
            name="uq_transfers_user_id_idempotency_key",
        ),
    )
    op.create_index(
        "ix_transfers_user_id_transaction_date",
        "transfers",
        ["user_id", "transaction_date"],
        unique=False,
    )

    op.add_column(
        "transactions",
        sa.Column("transfer_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_transactions_transfer_id_transfers",
        "transactions",
        "transfers",
        ["transfer_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_transactions_transfer_id",
        "transactions",
        ["transfer_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_transactions_transfer_id", table_name="transactions")
    op.drop_constraint(
        "fk_transactions_transfer_id_transfers",
        "transactions",
        type_="foreignkey",
    )
    op.drop_column("transactions", "transfer_id")
    op.drop_index(
        "ix_transfers_user_id_transaction_date",
        table_name="transfers",
    )
    op.drop_table("transfers")
