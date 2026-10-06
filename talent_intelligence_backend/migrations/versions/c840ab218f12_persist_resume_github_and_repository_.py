"""Persist resume github and repository analyses

Revision ID: c840ab218f12
Revises: b730cce208a1
Create Date: 2026-10-05 14:15:40.986395

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c840ab218f12'
down_revision = 'b730cce208a1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('github_analyses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('candidate_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('username', sa.String(length=255), nullable=True),
    sa.Column('total_public_repos', sa.Integer(), nullable=True),
    sa.Column('total_stars', sa.Integer(), nullable=True),
    sa.Column('candidate_attributed_commits', sa.Integer(), nullable=True),
    sa.Column('summary', sa.JSON(), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('candidate_id')
    )
    op.create_table('resume_analyses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('candidate_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('ats_score', sa.Float(), nullable=True),
    sa.Column('breakdown', sa.JSON(), nullable=True),
    sa.Column('missing_keywords', sa.JSON(), nullable=True),
    sa.Column('weak_areas', sa.JSON(), nullable=True),
    sa.Column('top_improvements', sa.JSON(), nullable=True),
    sa.Column('projects', sa.JSON(), nullable=True),
    sa.Column('final_verdict', sa.Text(), nullable=True),
    sa.Column('model_name', sa.String(length=100), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('candidate_id')
    )
    op.create_table('repository_analyses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('github_analysis_id', sa.Integer(), nullable=False),
    sa.Column('repo_name', sa.String(length=255), nullable=False),
    sa.Column('repo_url', sa.String(length=500), nullable=False),
    sa.Column('primary_language', sa.String(length=100), nullable=True),
    sa.Column('pushed_at', sa.DateTime(), nullable=True),
    sa.Column('score', sa.Float(), nullable=True),
    sa.Column('metrics', sa.JSON(), nullable=True),
    sa.Column('strengths', sa.JSON(), nullable=True),
    sa.Column('red_flags', sa.JSON(), nullable=True),
    sa.Column('recruiter_summary', sa.Text(), nullable=True),
    sa.Column('evidence_metadata', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['github_analysis_id'], ['github_analyses.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('github_analysis_id', 'repo_name', name='uq_analysis_repository')
    )

    # Existing applications gain empty records, never fabricated provider results.
    connection = op.get_bind()
    connection.execute(sa.text("""
        INSERT INTO resume_analyses (candidate_id, status, created_at, updated_at)
        SELECT id, 'pending', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP FROM candidates
    """))
    connection.execute(sa.text("""
        INSERT INTO github_analyses (candidate_id, status, username, created_at, updated_at)
        SELECT id, 'pending', github_username, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        FROM candidates WHERE github_username IS NOT NULL AND github_username <> ''
    """))


def downgrade():
    op.drop_table('repository_analyses')
    op.drop_table('resume_analyses')
    op.drop_table('github_analyses')
