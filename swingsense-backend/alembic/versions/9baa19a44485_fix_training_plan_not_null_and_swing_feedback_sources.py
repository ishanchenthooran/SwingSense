"""fix_training_plan_not_null_and_swing_feedback_sources

Revision ID: 9baa19a44485
Revises: 1dfaf7c2236f
Create Date: 2026-08-25 00:00:00.000000

Corrective migration: 56ae12611a5c and 1dfaf7c2236f were stamped as applied
without actually running against the real DB, and the real DB had drifted
from what those migrations describe:
  - training_plans.plan/years_played/handicap/strengths/weaknesses/goals
    exist but are nullable, not NOT NULL as 56ae12611a5c specifies.
  - swing_feedback.sources is missing entirely, though 1dfaf7c2236f adds it.
This migration brings the real schema in line with the model/migration
history without editing the already-stamped migration files.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9baa19a44485'
down_revision = '1dfaf7c2236f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('training_plans', 'plan', existing_type=sa.Text(), nullable=False)
    op.alter_column('training_plans', 'years_played', existing_type=sa.Integer(), nullable=False)
    op.alter_column('training_plans', 'handicap', existing_type=sa.Float(), nullable=False)
    op.alter_column('training_plans', 'strengths', existing_type=sa.Text(), nullable=False)
    op.alter_column('training_plans', 'weaknesses', existing_type=sa.Text(), nullable=False)
    op.alter_column('training_plans', 'goals', existing_type=sa.Text(), nullable=False)
    op.add_column('swing_feedback', sa.Column('sources', postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column('swing_feedback', 'sources')
    op.alter_column('training_plans', 'goals', existing_type=sa.Text(), nullable=True)
    op.alter_column('training_plans', 'weaknesses', existing_type=sa.Text(), nullable=True)
    op.alter_column('training_plans', 'strengths', existing_type=sa.Text(), nullable=True)
    op.alter_column('training_plans', 'handicap', existing_type=sa.Float(), nullable=True)
    op.alter_column('training_plans', 'years_played', existing_type=sa.Integer(), nullable=True)
    op.alter_column('training_plans', 'plan', existing_type=sa.Text(), nullable=True)
