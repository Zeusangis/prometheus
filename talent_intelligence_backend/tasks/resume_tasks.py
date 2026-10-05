from __future__ import annotations

from celery import shared_task
from flask import current_app
from PyPDF2 import PdfReader

from models import Candidate, db


def _extract_pdf_text(file_path: str) -> str:
    reader = PdfReader(file_path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


@shared_task(name="tasks.resume_tasks.process_resume_task", acks_late=True, reject_on_worker_lost=True)
def process_resume_task(candidate_id: int) -> dict:
    """Extraction checkpoint; job-aware provider analysis is not yet implemented."""
    candidate = db.session.get(Candidate, candidate_id)
    if not candidate:
        return {"status": "not_found", "candidate_id": candidate_id}
    candidate.analysis_status = "running"
    candidate.analysis_error = None
    db.session.commit()
    try:
        extracted_text = _extract_pdf_text(candidate.file_path)
        if not extracted_text:
            raise ValueError("No extractable text")
        candidate.raw_text = extracted_text
        # Parsing is useful evidence, but is not ATS or GitHub AI analysis.
        candidate.analysis_status = "partial"
        candidate.analysis_error = "Resume text extracted; AI analysis is not configured in this checkpoint."
        db.session.commit()
        return {"status": "partial", "candidate_id": candidate_id, "chars": len(extracted_text)}
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Resume extraction failed candidate_id=%s", candidate_id)
        candidate = db.session.get(Candidate, candidate_id)
        candidate.analysis_status = "failed"
        candidate.analysis_error = "Resume text could not be extracted. Retry or provide a readable PDF."
        db.session.commit()
        return {"status": "failed", "candidate_id": candidate_id}
