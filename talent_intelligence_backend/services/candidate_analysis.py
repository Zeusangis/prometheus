from flask import current_app

from models import Candidate, GitHubAnalysis, RepositoryAnalysis, ResumeAnalysis, db
from services.ai.gemini import InvalidProviderOutput, ProviderUnavailable
from services.resume.analyzer import analyze_resume
from services.github.analyzer import analyze_github
from services.github.client import GitHubUnavailable


def ensure_records(candidate):
    if candidate.resume_analysis is None:
        candidate.resume_analysis = ResumeAnalysis(status="pending")
    if candidate.github_username and candidate.github_analysis is None:
        candidate.github_analysis = GitHubAnalysis(status="pending", username=candidate.github_username)
    db.session.flush()


def prepare_retry(candidate):
    ensure_records(candidate)
    for component in (candidate.resume_analysis, candidate.github_analysis):
        if component and component.status != "complete":
            component.status = "pending"
            component.error_message = None


def overall_status(resume_status, github_status=None):
    statuses = [resume_status] + ([github_status] if github_status is not None else [])
    if all(status == "complete" for status in statuses):
        return "complete"
    if "complete" in statuses or "partial" in statuses:
        return "partial"
    return "failed"


def process_analysis(candidate_id, extract_text):
    candidate = db.session.get(Candidate, candidate_id)
    if not candidate:
        return {"status": "not_found", "candidate_id": candidate_id}
    ensure_records(candidate)
    if candidate.analysis_status == "complete":
        return {"status": "complete", "candidate_id": candidate_id}
    candidate.analysis_status = "running"
    candidate.analysis_error = None
    resume = candidate.resume_analysis
    if resume.status != "complete":
        resume.status = "running"
        resume.error_message = None
    db.session.commit()
    try:
        # Partial retries must not pay for or overwrite an already-complete component.
        if resume.status != "complete":
            text = extract_text(candidate.file_path)
            if not text:
                raise ValueError("Resume has no extractable text")
            candidate.raw_text = text
            db.session.commit()
            if not candidate.job:
                raise ProviderUnavailable("Resume analysis requires a linked job.")
            result, model = analyze_resume(text, candidate.job)
            for key, value in result.items():
                setattr(resume, key, value)
            resume.model_name = model
            resume.status = "complete"
            candidate.ats_score = result["ats_score"]
            db.session.commit()
    except Exception as error:
        db.session.rollback()
        current_app.logger.warning("Resume analysis failed candidate_id=%s type=%s", candidate_id, type(error).__name__)
        candidate = db.session.get(Candidate, candidate_id)
        resume = candidate.resume_analysis
        resume.status = "failed"
        resume.error_message = str(error) if isinstance(error, (ProviderUnavailable, InvalidProviderOutput)) else "Resume analysis could not be completed. Retry or provide a readable PDF."
        # Never expose stale successful scores as current failed analysis.
        for key in ("ats_score", "breakdown", "missing_keywords", "weak_areas", "top_improvements", "projects", "final_verdict", "model_name"):
            setattr(resume, key, None)
        candidate.ats_score = None
        db.session.commit()

    github = candidate.github_analysis
    if github and github.status != "complete":
        github.status = "running"
        github.error_message = None
        db.session.commit()
        try:
            result = analyze_github(candidate.github_username, candidate.job)
            for key in ("status", "username", "total_public_repos", "total_stars", "candidate_attributed_commits", "summary", "error_message"):
                setattr(github, key, result[key])
            # Delete old sampled outputs before replacement to honor repository uniqueness.
            github.repositories.clear()
            db.session.flush()
            github.repositories.extend(RepositoryAnalysis(**repo) for repo in result["repositories"])
            db.session.commit()
        except Exception as error:
            db.session.rollback()
            current_app.logger.warning("GitHub analysis failed candidate_id=%s type=%s", candidate_id, type(error).__name__)
            candidate = db.session.get(Candidate, candidate_id)
            resume, github = candidate.resume_analysis, candidate.github_analysis
            github.status = "failed"
            github.error_message = str(error) if isinstance(error, GitHubUnavailable) else "GitHub analysis could not be completed. Retry later."
            for key in ("total_public_repos", "total_stars", "candidate_attributed_commits", "summary"):
                setattr(github, key, None)
            github.repositories.clear()
            db.session.commit()
    candidate.analysis_status = overall_status(resume.status, github.status if github else None)
    candidate.analysis_error = None if candidate.analysis_status == "complete" else "Some analysis could not be completed. Review component statuses and retry."
    db.session.commit()
    return {"status": candidate.analysis_status, "candidate_id": candidate_id}
