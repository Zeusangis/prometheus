from pathlib import Path

from flask_migrate import check, upgrade
from sqlalchemy import text

from app import create_app
from models import Job, Organization, OrganizationMembership, User, db

MIGRATIONS = str(Path(__file__).resolve().parents[1] / "migrations")


def test_bootstrap_cli(app):
    result = app.test_cli_runner().invoke(args=[
        "create-recruiter", "--email", "new@example.invalid", "--name", "New Test Recruiter",
        "--organization", "New Test Organization",
    ], input="bootstrap-test-password\nbootstrap-test-password\n")
    assert result.exit_code == 0, result.output
    with app.app_context():
        user = db.session.scalar(db.select(User).where(User.email == "new@example.invalid"))
        assert user.check_password("bootstrap-test-password")
        assert db.session.scalar(db.select(OrganizationMembership).where(OrganizationMembership.user_id == user.id))


def test_legacy_jobs_are_quarantined_and_explicitly_claimed(tmp_path):
    app = create_app({
        "TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(tmp_path / "legacy.sqlite"),
        "UPLOAD_FOLDER": str(tmp_path / "uploads"),
    })
    with app.app_context():
        upgrade(directory=MIGRATIONS, revision="a62b9e41d037")
        db.session.execute(text("INSERT INTO jobs (id, title, company, status) VALUES (1, 'Legacy Test Role', 'Old Test Company', 'open')"))
        db.session.commit()
        upgrade(directory=MIGRATIONS)
        legacy = db.session.get(Job, 1)
        assert legacy.title == "Legacy Test Role"
        assert db.session.get(Organization, legacy.organization_id).name == "Unclaimed legacy data"
        assert OrganizationMembership.query.count() == 0
        org = Organization(name="Claiming Test Organization")
        db.session.add(org)
        db.session.commit()
        org_id = org.id
        check(directory=MIGRATIONS)
    result = app.test_cli_runner().invoke(args=["assign-legacy-job", "--job-id", "1", "--organization-id", str(org_id), "--yes"])
    assert result.exit_code == 0, result.output
    with app.app_context():
        assert db.session.get(Job, 1).organization_id == org_id
        db.session.remove()
        db.engine.dispose()
