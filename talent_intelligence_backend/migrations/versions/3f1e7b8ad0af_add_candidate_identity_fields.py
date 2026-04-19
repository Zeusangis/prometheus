"""Add candidate identity fields

Revision ID: 3f1e7b8ad0af
Revises: 8d7e60f130e2
Create Date: 2026-04-18 20:58:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3f1e7b8ad0af"
down_revision = "8d7e60f130e2"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("candidates", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("full_name", sa.String(length=255), nullable=True)
        )
        batch_op.add_column(sa.Column("email", sa.String(length=255), nullable=True))
        batch_op.add_column(
            sa.Column("github_username", sa.String(length=255), nullable=True)
        )


def downgrade():
    with op.batch_alter_table("candidates", schema=None) as batch_op:
        batch_op.drop_column("github_username")
        batch_op.drop_column("email")
        batch_op.drop_column("full_name")
