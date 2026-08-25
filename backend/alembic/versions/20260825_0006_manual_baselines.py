"""manual baselines for processing-time comparison

Revision ID: 0006_manual_baselines
Revises: 0005_correction_records
Create Date: 2026-08-25

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006_manual_baselines"
down_revision: Union[str, Sequence[str], None] = "0005_correction_records"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "manual_baselines",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("factory_id", sa.Uuid(), nullable=False),
        sa.Column("part_description", sa.String(length=200), nullable=False),
        sa.Column("manual_duration_seconds", sa.Integer(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_by_user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["factory_id"], ["factories.id"]),
        sa.ForeignKeyConstraint(["recorded_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_manual_baselines_factory_id", "manual_baselines", ["factory_id"])


def downgrade() -> None:
    op.drop_index("ix_manual_baselines_factory_id", table_name="manual_baselines")
    op.drop_table("manual_baselines")
