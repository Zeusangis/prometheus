"""Add meeting tracking to candidates

Revision ID: d84b7a9c11f2
Revises: 3f1e7b8ad0af
Create Date: 2026-04-19 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d84b7a9c11f2"
down_revision = "3f1e7b8ad0af"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("candidates", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("meeting_id", sa.String(length=255), nullable=True)
        )

    op.create_table(
        "meeting_summaries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("candidate_id", sa.Integer(), nullable=False),
        sa.Column("meeting_id", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=True, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"]),
        sa.UniqueConstraint("meeting_id"),
    )


def downgrade():
    op.drop_table("meeting_summaries")

    with op.batch_alter_table("candidates", schema=None) as batch_op:
        batch_op.drop_column("meeting_id")
