"""tenant delete confirmation challenges

Revision ID: 0011_tenant_data_export_delete
Revises: 0010_admin_accounts_preferences
Create Date: 2026-08-25

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011_tenant_data_export_delete"
down_revision: Union[str, Sequence[str], None] = "0010_admin_accounts_preferences"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tenant_delete_challenges",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("factory_id", sa.Uuid(), nullable=False),
        sa.Column("token", sa.String(length=128), nullable=False),
        sa.Column("required_phrase", sa.String(length=200), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["factory_id"], ["factories.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token", name="uq_tenant_delete_challenges_token"),
    )
    op.create_index(
        op.f("ix_tenant_delete_challenges_factory_id"),
        "tenant_delete_challenges",
        ["factory_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_tenant_delete_challenges_factory_id"), table_name="tenant_delete_challenges"
    )
    op.drop_table("tenant_delete_challenges")
