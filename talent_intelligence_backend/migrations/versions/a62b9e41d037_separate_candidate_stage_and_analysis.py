"""Separate recruiting stages from asynchronous analysis status.

Revision ID: a62b9e41d037
Revises: f87109fe65cc
"""
from alembic import op
import sqlalchemy as sa

revision = "a62b9e41d037"
down_revision = "f87109fe65cc"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("candidates") as batch:
        batch.add_column(sa.Column("analysis_status", sa.String(50), nullable=True))
        batch.add_column(sa.Column("analysis_error", sa.Text(), nullable=True))
    # Existing 'processed' means text extraction only, not completed AI scoring.
    op.execute(sa.text("""
        UPDATE candidates SET analysis_status = CASE
            WHEN status = 'failed' THEN 'failed'
            WHEN status IN ('processed', 'ats_scored') OR raw_text IS NOT NULL THEN 'partial'
            ELSE 'queued' END
    """))
    op.execute(sa.text("""
        UPDATE candidates SET status = 'screening'
        WHERE status IS NULL OR status NOT IN
        ('screening', 'interview_scheduled', 'interview_completed', 'offer_made', 'hired', 'rejected')
    """))
    op.execute(sa.text("""
        UPDATE candidates SET analysis_error =
        'Previous resume processing failed. Retry analysis.' WHERE analysis_status = 'failed'
    """))
    with op.batch_alter_table("candidates") as batch:
        batch.alter_column("analysis_status", existing_type=sa.String(50), nullable=False)
        batch.alter_column("status", existing_type=sa.String(50), nullable=False)


def downgrade():
    op.execute(sa.text("""
        UPDATE candidates SET status = CASE
            WHEN analysis_status = 'failed' THEN 'failed'
            WHEN analysis_status IN ('partial', 'complete') THEN 'processed'
            ELSE 'queued' END
        WHERE status = 'screening'
    """))
    with op.batch_alter_table("candidates") as batch:
        batch.alter_column("status", existing_type=sa.String(50), nullable=True)
        batch.drop_column("analysis_error")
        batch.drop_column("analysis_status")
