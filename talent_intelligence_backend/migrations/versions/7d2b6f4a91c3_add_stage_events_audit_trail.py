"""Add the stage events audit trail

Revision ID: 7d2b6f4a91c3
Revises: c840ab218f12
Create Date: 2026-10-06 09:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7d2b6f4a91c3'
down_revision = 'c840ab218f12'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('stage_events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('candidate_id', sa.Integer(), nullable=False),
    sa.Column('job_id', sa.Integer(), nullable=True),
    sa.Column('event_type', sa.String(length=50), nullable=False),
    sa.Column('from_stage', sa.String(length=50), nullable=True),
    sa.Column('to_stage', sa.String(length=50), nullable=True),
    sa.Column('previous_analysis_status', sa.String(length=50), nullable=True),
    sa.Column('actor_user_id', sa.Integer(), nullable=True),
    sa.Column('actor_email', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ),
    sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
    sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    # Backfill only what the code currently records: the recruiting stage a candidate
    # holds today. No actor, timestamp or intermediate stage is invented, and nothing is
    # written for candidates that never left screening. uploaded_at can be null on legacy
    # rows, so the migration timestamp is used rather than an invalid null.
    connection = op.get_bind()
    connection.execute(sa.text("""
        INSERT INTO stage_events (candidate_id, job_id, event_type, to_stage, created_at)
        SELECT id, job_id, 'stage_changed', status, COALESCE(uploaded_at, CURRENT_TIMESTAMP)
        FROM candidates
        WHERE status IS NOT NULL AND status <> 'screening'
    """))


def downgrade():
    op.drop_table('stage_events')
