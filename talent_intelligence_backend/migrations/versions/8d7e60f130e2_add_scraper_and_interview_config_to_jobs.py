"""Add scraper and interview config to jobs

Revision ID: 8d7e60f130e2
Revises: 50a0b0555add
Create Date: 2026-04-18 20:31:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8d7e60f130e2"
down_revision = "50a0b0555add"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("jobs", schema=None) as batch_op:
        batch_op.add_column(sa.Column("scraper_config", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("interview_config", sa.JSON(), nullable=True))


def downgrade():
    with op.batch_alter_table("jobs", schema=None) as batch_op:
        batch_op.drop_column("interview_config")
        batch_op.drop_column("scraper_config")
