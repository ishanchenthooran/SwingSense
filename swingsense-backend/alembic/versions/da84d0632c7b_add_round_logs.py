"""add_round_logs

Revision ID: da84d0632c7b
Revises: cb5464379693
Create Date: 2026-08-20 21:34:11.445626

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'da84d0632c7b'
down_revision = 'cb5464379693'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'round_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('round_date', sa.Date(), nullable=False),
        sa.Column('course_name', sa.Text(), nullable=True),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('score_to_par', sa.Integer(), nullable=True),
        sa.Column('putts', sa.Integer(), nullable=True),
        sa.Column('fairways_hit', sa.Integer(), nullable=True),
        sa.Column('greens_in_regulation', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_round_logs_user_id', 'round_logs', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_round_logs_user_id', table_name='round_logs')
    op.drop_table('round_logs')
