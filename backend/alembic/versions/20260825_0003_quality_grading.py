"""quality grading: part drawing status, grade, and timestamped events

Revision ID: 0003_quality_grading
Revises: 0002_upload_drawing
Create Date: 2026-08-25

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_quality_grading"
down_revision: Union[str, Sequence[str], None] = "0002_upload_drawing"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "part_drawings",
        sa.Column("status", sa.String(length=20), nullable=False, server_default="已上传"),
    )
    op.add_column(
        "part_drawings",
        sa.Column("quality_grade", sa.String(length=10), nullable=True),
    )
    op.add_column(
        "part_drawings",
        sa.Column("is_assembly_or_exploded", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "part_drawings",
        sa.Column("low_quality_unreliable", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("part_drawings", "status", server_default=None)
    op.alter_column("part_drawings", "is_assembly_or_exploded", server_default=None)
    op.alter_column("part_drawings", "low_quality_unreliable", server_default=None)

    op.create_table(
        "part_drawing_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("part_drawing_id", sa.Uuid(), nullable=False),
        sa.Column("factory_id", sa.Uuid(), nullable=False),
        sa.Column("from_status", sa.String(length=20), nullable=True),
        sa.Column("to_status", sa.String(length=20), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sequence_no", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["part_drawing_id"], ["part_drawings.id"]),
        sa.ForeignKeyConstraint(["factory_id"], ["factories.id"]),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("part_drawing_id", "sequence_no", name="uq_part_drawing_events_sequence"),
    )
    op.create_index(
        "ix_part_drawing_events_part_drawing_id",
        "part_drawing_events",
        ["part_drawing_id"],
    )
    op.create_index(
        "ix_part_drawing_events_factory_id",
        "part_drawing_events",
        ["factory_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_part_drawing_events_factory_id", table_name="part_drawing_events")
    op.drop_index("ix_part_drawing_events_part_drawing_id", table_name="part_drawing_events")
    op.drop_table("part_drawing_events")
    op.drop_column("part_drawings", "low_quality_unreliable")
    op.drop_column("part_drawings", "is_assembly_or_exploded")
    op.drop_column("part_drawings", "quality_grade")
    op.drop_column("part_drawings", "status")
