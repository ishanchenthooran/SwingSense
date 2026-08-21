"""add_user_profiles

Revision ID: cb5464379693
Revises: 1dfaf7c2236f
Create Date: 2026-08-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'cb5464379693'
down_revision = '1dfaf7c2236f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'user_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('name', sa.Text(), nullable=True),
        sa.Column('years_played', sa.Integer(), nullable=True),
        sa.Column('handicap', sa.Float(), nullable=True),
        sa.Column('skill_level', sa.Text(), nullable=True),
        sa.Column('goals', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('user_profiles')
