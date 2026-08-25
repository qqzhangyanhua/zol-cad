"""quote tasks: light grouping layer for part drawings

Revision ID: 0008_quote_tasks
Revises: 0007_part_family
Create Date: 2026-08-25

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008_quote_tasks"
down_revision: Union[str, Sequence[str], None] = "0007_part_family"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "quote_tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("factory_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("customer_name", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["factory_id"], ["factories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_quote_tasks_factory_id", "quote_tasks", ["factory_id"])
    op.create_index("ix_quote_tasks_created_at", "quote_tasks", ["created_at"])
    op.create_index("ix_quote_tasks_customer_name", "quote_tasks", ["customer_name"])
    op.add_column(
        "part_drawings",
        sa.Column("quote_task_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_part_drawings_quote_task_id",
        "part_drawings",
        "quote_tasks",
        ["quote_task_id"],
        ["id"],
    )
    op.create_index("ix_part_drawings_quote_task_id", "part_drawings", ["quote_task_id"])


def downgrade() -> None:
    op.drop_index("ix_part_drawings_quote_task_id", table_name="part_drawings")
    op.drop_constraint("fk_part_drawings_quote_task_id", "part_drawings", type_="foreignkey")
    op.drop_column("part_drawings", "quote_task_id")
    op.drop_index("ix_quote_tasks_customer_name", table_name="quote_tasks")
    op.drop_index("ix_quote_tasks_created_at", table_name="quote_tasks")
    op.drop_index("ix_quote_tasks_factory_id", table_name="quote_tasks")
    op.drop_table("quote_tasks")
