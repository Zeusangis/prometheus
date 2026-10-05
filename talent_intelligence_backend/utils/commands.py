import click
from flask import current_app

from models import Job, Organization, OrganizationMembership, User, db


def register_commands(app):
    @app.cli.command("create-recruiter")
    @click.option("--email", required=True)
    @click.option("--name", required=True)
    @click.option("--organization", required=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_recruiter(email, name, organization, password):
        """Create a recruiter and a new organization; no implicit legacy data access."""
        email = email.strip().lower()
        if db.session.scalar(db.select(User).where(User.email == email)):
            raise click.ClickException("A user with this email already exists.")
        user = User(email=email, name=name.strip())
        try:
            user.set_password(password)
        except ValueError as error:
            raise click.ClickException(str(error)) from error
        org = Organization(name=organization.strip())
        db.session.add_all([user, org])
        db.session.flush()
        db.session.add(OrganizationMembership(user_id=user.id, organization_id=org.id, role="owner"))
        db.session.commit()
        click.echo(f"Created recruiter and organization {org.id}.")

    @app.cli.command("assign-legacy-job")
    @click.option("--job-id", required=True, type=int)
    @click.option("--organization-id", required=True, type=int)
    @click.confirmation_option(prompt="Assign this unclaimed legacy job to the specified organization?")
    def assign_legacy_job(job_id, organization_id):
        """Operator-only ownership repair; never guess ownership from old JSON."""
        job = db.session.get(Job, job_id)
        org = db.session.get(Organization, organization_id)
        old_org = db.session.get(Organization, job.organization_id) if job else None
        if not job or not org or not old_org or old_org.name != "Unclaimed legacy data":
            raise click.ClickException("Job must be unclaimed and target organization must exist.")
        job.organization_id = org.id
        db.session.commit()
        current_app.logger.warning("Legacy ownership assigned job_id=%s organization_id=%s", job.id, org.id)
        click.echo("Ownership assigned.")
