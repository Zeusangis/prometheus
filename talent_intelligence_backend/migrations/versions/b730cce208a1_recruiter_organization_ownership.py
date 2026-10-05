"""Recruiter identities and explicit organization ownership.

Revision ID: b730cce208a1
Revises: a62b9e41d037
"""
from alembic import op
import sqlalchemy as sa

revision = "b730cce208a1"
down_revision = "a62b9e41d037"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(500), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("session_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table("organizations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table("organization_memberships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("role", sa.String(30), nullable=False),
        sa.UniqueConstraint("user_id", "organization_id", name="uq_membership_user_org"),
    )
    op.create_index("ix_organization_memberships_user_id", "organization_memberships", ["user_id"])
    op.create_index("ix_organization_memberships_organization_id", "organization_memberships", ["organization_id"])
    with op.batch_alter_table("jobs") as batch:
        batch.add_column(sa.Column("organization_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("created_by_user_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_jobs_organization_id", "organizations", ["organization_id"], ["id"])
        batch.create_foreign_key("fk_jobs_created_by_user", "users", ["created_by_user_id"], ["id"])
    connection = op.get_bind()
    # Never infer ownership from untrusted legacy recruiter JSON/company names.
    if connection.execute(sa.text("SELECT COUNT(*) FROM jobs")).scalar():
        connection.execute(sa.text("INSERT INTO organizations (id, name, created_at) VALUES (1, 'Unclaimed legacy data', CURRENT_TIMESTAMP)"))
        connection.execute(sa.text("UPDATE jobs SET organization_id = 1"))
    with op.batch_alter_table("jobs") as batch:
        batch.alter_column("organization_id", existing_type=sa.Integer(), nullable=False)
        batch.create_index("ix_jobs_organization_id", ["organization_id"])


def downgrade():
    with op.batch_alter_table("jobs") as batch:
        batch.drop_index("ix_jobs_organization_id")
        batch.drop_constraint("fk_jobs_organization_id", type_="foreignkey")
        batch.drop_constraint("fk_jobs_created_by_user", type_="foreignkey")
        batch.drop_column("organization_id")
        batch.drop_column("created_by_user_id")
    op.drop_index("ix_organization_memberships_user_id", table_name="organization_memberships")
    op.drop_index("ix_organization_memberships_organization_id", table_name="organization_memberships")
    op.drop_table("organization_memberships")
    op.drop_table("organizations")
    op.drop_table("users")
