"""add_sources_to_feedback

Revision ID: 1dfaf7c2236f
Revises: 56ae12611a5c
Create Date: 2026-04-21 17:01:41.540258

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '1dfaf7c2236f'
down_revision = '56ae12611a5c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('swing_feedback',
        sa.Column('sources', postgresql.JSONB(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('swing_feedback', 'sources')
