"""stash first extract so 差图仍然继续 does not call the engine again

Revision ID: 0012_stashed_extracted_fields
Revises: 0011_tenant_data_export_delete
Create Date: 2026-08-26

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0012_stashed_extracted_fields"
down_revision: Union[str, Sequence[str], None] = "0011_tenant_data_export_delete"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "part_drawings",
        sa.Column("stashed_extracted_fields", JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("part_drawings", "stashed_extracted_fields")
