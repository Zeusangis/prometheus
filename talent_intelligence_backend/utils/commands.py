import os

import click
from flask import current_app

from models import Job, Organization, OrganizationMembership, User, db
from services.ai.gemini import generate_json, provider_status


def register_commands(app):
    @app.cli.command("check-analysis")
    @click.option("--live", is_flag=True, help="Also perform one real AI provider call (costs a token).")
    @click.option("--github-username", default="", help="Also collect real GitHub evidence for this username.")
    def check_analysis(live, github_username):
        """Report what resume and GitHub analysis need, and optionally prove them live.

        Nothing here prints or stores a credential.
        """
        status = provider_status()
        click.echo("Resume analysis:")
        if status["resume_provider_configured"]:
            click.echo(f"  GEMINI_API_KEY: configured (model {status['resume_model']})")
        else:
            click.echo("  GEMINI_API_KEY: MISSING - resume analysis will fail for every applicant")
            click.echo("  Add GEMINI_API_KEY=<key> to talent_intelligence_backend/.env and restart the worker.")
        click.echo(f"  GITHUB_TOKEN: {'configured' if os.environ.get('GITHUB_TOKEN', '').strip() else 'not set (optional; public rate limits apply)'}")

        broker = app.config.get("CELERY", {}).get("broker_url", "")
        click.echo(f"Task broker: {broker}")
        if broker.startswith("redis://"):
            try:
                import redis

                client = redis.from_url(broker, socket_connect_timeout=3, socket_timeout=3)
                client.ping()
                client.close()
                click.echo("  broker reachable: yes")
            except Exception as error:  # noqa: BLE001 - operator diagnostics
                click.echo(f"  broker reachable: no ({type(error).__name__})")
                click.echo("  Start Redis and a worker: celery -A app.celery_app worker --loglevel=info")
        click.echo("  A worker must be running or applications stay queued; retry after starting it.")

        if not live and not github_username:
            return
        if live:
            click.echo("Live provider call:")
            try:
                value, model = generate_json(
                    'Return JSON matching the schema with ok set to true.',
                    {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"]},
                )
                click.echo(f"  {model}: replied {value}")
            except Exception as error:  # noqa: BLE001 - operator diagnostics
                click.echo(f"  failed: {error}")
        if github_username:
            from services.github.collector import collect_github

            click.echo(f"Live GitHub collection for {github_username}:")
            try:
                evidence = collect_github(github_username)
                click.echo(
                    f"  listed {evidence['summary']['listed_repos']}, analyzed "
                    f"{len(evidence['repositories'])}, errors {evidence['summary']['errors']}"
                )
            except Exception as error:  # noqa: BLE001 - operator diagnostics
                click.echo(f"  failed: {error}")

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
