"""add unique constraint for youtube chunks upsert

Revision ID: 400d70b6d4fb
Revises: ede2469b7093
Create Date: 2025-06-15 07:47:43.546019

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '400d70b6d4fb'
down_revision: Union[str, None] = 'ede2469b7093'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add unique constraint for upsert operations
    op.create_unique_constraint(
        'unique_project_video_chunk',
        'youtube_chunks',
        ['project_slug', 'video_id', 'chunk_index']
    )


def downgrade() -> None:
    # Drop unique constraint
    op.drop_constraint('unique_project_video_chunk', 'youtube_chunks', type_='unique')