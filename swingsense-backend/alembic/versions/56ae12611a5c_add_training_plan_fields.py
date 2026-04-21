"""add_training_plan_fields

Revision ID: 56ae12611a5c
Revises: 64fa8ce4e6af
Create Date: 2025-09-10 18:48:44.537887

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '56ae12611a5c'
down_revision = '64fa8ce4e6af'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('training_plans', 'plan',
                    existing_type=postgresql.JSONB(astext_type=sa.Text()),
                    type_=sa.Text(),
                    existing_nullable=True,
                    nullable=False,
                    postgresql_using='plan::text')
    op.add_column('training_plans', sa.Column('years_played', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('training_plans', sa.Column('handicap', sa.Float(), nullable=False, server_default='0'))
    op.add_column('training_plans', sa.Column('strengths', sa.Text(), nullable=False, server_default=''))
    op.add_column('training_plans', sa.Column('weaknesses', sa.Text(), nullable=False, server_default=''))
    op.add_column('training_plans', sa.Column('goals', sa.Text(), nullable=False, server_default=''))
    # Remove server defaults — they were only needed to satisfy NOT NULL on existing rows
    op.alter_column('training_plans', 'years_played', server_default=None)
    op.alter_column('training_plans', 'handicap', server_default=None)
    op.alter_column('training_plans', 'strengths', server_default=None)
    op.alter_column('training_plans', 'weaknesses', server_default=None)
    op.alter_column('training_plans', 'goals', server_default=None)


def downgrade() -> None:
    op.drop_column('training_plans', 'goals')
    op.drop_column('training_plans', 'weaknesses')
    op.drop_column('training_plans', 'strengths')
    op.drop_column('training_plans', 'handicap')
    op.drop_column('training_plans', 'years_played')
    op.alter_column('training_plans', 'plan',
                    existing_type=sa.Text(),
                    type_=postgresql.JSONB(astext_type=sa.Text()),
                    existing_nullable=False,
                    nullable=True,
                    postgresql_using='plan::jsonb')
