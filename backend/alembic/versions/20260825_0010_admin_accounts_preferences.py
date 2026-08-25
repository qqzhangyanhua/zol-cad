"""admin accounts, factory preferences

Revision ID: 0010_admin_accounts_preferences
Revises: 0009_quote_sheet_templates
Create Date: 2026-08-25

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010_admin_accounts_preferences"
down_revision: Union[str, Sequence[str], None] = "0009_quote_sheet_templates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True))
    op.create_table(
        "factory_preferences",
        sa.Column("factory_id", sa.Uuid(), nullable=False),
        sa.Column("common_materials", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("risk_label_priority", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(["factory_id"], ["factories.id"]),
        sa.PrimaryKeyConstraint("factory_id"),
    )


def downgrade() -> None:
    op.drop_table("factory_preferences")
    op.drop_column("users", "disabled_at")
