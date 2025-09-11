"""init schema

Revision ID: 64fa8ce4e6af
Revises: 
Create Date: 2025-09-07 19:47:29.313232

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '64fa8ce4e6af'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    create extension if not exists "uuid-ossp";

    create table if not exists users(
        id uuid primary key default uuid_generate_v4(),
        email text unique not null,
        hashed_password text not null,
        created_at timestamptz default now()
    );

    create table if not exists profiles(
        id uuid primary key default uuid_generate_v4(),
        user_id uuid references users(id),
        username text unique not null,
        handicap integer,
        strengths text,
        weaknesses text
    );

    create table if not exists swing_questions(
        id uuid primary key default uuid_generate_v4(),
        user_id uuid references users(id),
        question text,
        created_at timestamptz default now()
    );

    create table if not exists swing_feedback(
        id uuid primary key default uuid_generate_v4(),
        question_id uuid references swing_questions(id),
        feedback text,
        created_at timestamptz default now()
    );

    create table if not exists training_plans(
        id uuid primary key default uuid_generate_v4(),
        user_id uuid references users(id),
        plan jsonb,
        created_at timestamptz default now()
    );

    create table if not exists progress_metrics(
        id uuid primary key default uuid_generate_v4(),
        user_id uuid references users(id),
        metric jsonb,
        created_at timestamptz default now()
    );

    create table if not exists resources(
        id uuid primary key default uuid_generate_v4(),
        issue text,
        url text
    );
    """)

def downgrade():
    op.execute("""
    drop table if exists resources;
    drop table if exists progress_metrics;
    drop table if exists training_plans;
    drop table if exists swing_feedback;
    drop table if exists swing_questions;
    drop table if exists profiles;
    drop table if exists users;
    """)
