"""upload drawing: storage metadata on part_drawings

Revision ID: 0002_upload_drawing
Revises: 0001_walking_skeleton
Create Date: 2026-08-25

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_upload_drawing"
down_revision: Union[str, Sequence[str], None] = "0001_walking_skeleton"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "part_drawings",
        sa.Column("storage_key", sa.String(length=800), nullable=False, server_default=""),
    )
    op.add_column(
        "part_drawings",
        sa.Column(
            "content_type",
            sa.String(length=100),
            nullable=False,
            server_default="application/octet-stream",
        ),
    )
    op.add_column(
        "part_drawings",
        sa.Column("byte_size", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "part_drawings",
        sa.Column("page_count", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "part_drawings",
        sa.Column("selected_page", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "part_drawings",
        sa.Column("uploaded_by_user_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_part_drawings_uploaded_by_user_id",
        "part_drawings",
        "users",
        ["uploaded_by_user_id"],
        ["id"],
    )
    op.create_index(
        "ix_part_drawings_uploaded_by_user_id",
        "part_drawings",
        ["uploaded_by_user_id"],
    )
    op.alter_column("part_drawings", "storage_key", server_default=None)
    op.alter_column("part_drawings", "content_type", server_default=None)
    op.alter_column("part_drawings", "byte_size", server_default=None)
    op.alter_column("part_drawings", "page_count", server_default=None)
    op.alter_column("part_drawings", "selected_page", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_part_drawings_uploaded_by_user_id", table_name="part_drawings")
    op.drop_constraint("fk_part_drawings_uploaded_by_user_id", "part_drawings", type_="foreignkey")
    op.drop_column("part_drawings", "uploaded_by_user_id")
    op.drop_column("part_drawings", "selected_page")
    op.drop_column("part_drawings", "page_count")
    op.drop_column("part_drawings", "byte_size")
    op.drop_column("part_drawings", "content_type")
    op.drop_column("part_drawings", "storage_key")
