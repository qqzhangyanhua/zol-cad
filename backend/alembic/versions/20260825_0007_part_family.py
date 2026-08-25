"""persist part family on each drawing

Revision ID: 0007_part_family
Revises: 0006_manual_baselines
Create Date: 2026-08-25

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007_part_family"
down_revision: Union[str, Sequence[str], None] = "0006_manual_baselines"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "part_drawings",
        sa.Column(
            "part_family_id",
            sa.String(length=80),
            nullable=False,
            server_default="unknown",
        ),
    )
    op.alter_column("part_drawings", "part_family_id", server_default=None)


def downgrade() -> None:
    op.drop_column("part_drawings", "part_family_id")
