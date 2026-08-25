"""immutable correction records

Revision ID: 0005_correction_records
Revises: 0004_extraction
Create Date: 2026-08-25

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_correction_records"
down_revision: Union[str, Sequence[str], None] = "0004_extraction"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "correction_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("factory_id", sa.Uuid(), nullable=False),
        sa.Column("part_drawing_id", sa.Uuid(), nullable=False),
        sa.Column("field_key", sa.String(length=80), nullable=False),
        sa.Column("field_type", sa.String(length=40), nullable=False),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("actor_user_id", sa.Uuid(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["factory_id"], ["factories.id"]),
        sa.ForeignKeyConstraint(["part_drawing_id"], ["part_drawings.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_correction_records_factory_id"),
        "correction_records",
        ["factory_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_correction_records_part_drawing_id"),
        "correction_records",
        ["part_drawing_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_correction_records_part_drawing_id"), table_name="correction_records")
    op.drop_index(op.f("ix_correction_records_factory_id"), table_name="correction_records")
    op.drop_table("correction_records")
