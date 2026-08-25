"""extraction snapshot and failure reason on part drawings

Revision ID: 0004_extraction
Revises: 0003_quality_grading
Create Date: 2026-08-25

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0004_extraction"
down_revision: Union[str, Sequence[str], None] = "0003_quality_grading"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "part_drawings",
        sa.Column("extracted_fields", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
    )
    op.add_column(
        "part_drawings",
        sa.Column("extraction_failure_reason", sa.Text(), nullable=True),
    )
    op.alter_column("part_drawings", "extracted_fields", server_default=None)


def downgrade() -> None:
    op.drop_column("part_drawings", "extraction_failure_reason")
    op.drop_column("part_drawings", "extracted_fields")
