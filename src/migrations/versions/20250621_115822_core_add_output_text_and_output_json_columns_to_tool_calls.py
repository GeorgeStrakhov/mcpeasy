"""add output_text and output_json columns to tool_calls

Revision ID: 20250621_115822_core
Revises: 400d70b6d4fb
Create Date: 2025-06-21 11:58:22.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20250621_115822_core'
down_revision: Union[str, None] = '400d70b6d4fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tool_calls', sa.Column('output_text', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('tool_calls', sa.Column('output_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    
    # Migrate existing data from output_data to output_text
    op.execute("""
        UPDATE tool_calls 
        SET output_text = output_data 
        WHERE output_data IS NOT NULL
    """)
    
    # Drop the old output_data column
    op.drop_column('tool_calls', 'output_data')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # Add back the old output_data column
    op.add_column('tool_calls', sa.Column('output_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    
    # Migrate data back to output_data (prefer output_json, fallback to output_text)
    op.execute("""
        UPDATE tool_calls 
        SET output_data = COALESCE(output_json, output_text)
        WHERE output_json IS NOT NULL OR output_text IS NOT NULL
    """)
    
    op.drop_column('tool_calls', 'output_json')
    op.drop_column('tool_calls', 'output_text')
    # ### end Alembic commands ###