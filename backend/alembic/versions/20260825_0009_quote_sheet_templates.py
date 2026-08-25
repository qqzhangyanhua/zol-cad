"""quote sheet templates: backend-maintained per-factory column config

Revision ID: 0009_quote_sheet_templates
Revises: 0008_quote_tasks
Create Date: 2026-08-25

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009_quote_sheet_templates"
down_revision: Union[str, Sequence[str], None] = "0008_quote_tasks"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "quote_sheet_templates",
        sa.Column("factory_id", sa.Uuid(), nullable=False),
        sa.Column("columns", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(["factory_id"], ["factories.id"]),
        sa.PrimaryKeyConstraint("factory_id"),
    )


def downgrade() -> None:
    op.drop_table("quote_sheet_templates")
