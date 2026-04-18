from __future__ import annotations

from celery import shared_task
from PyPDF2 import PdfReader

from models import Candidate, db


def _extract_pdf_text(file_path: str) -> str:
    """Extract raw text from a PDF file path."""
    reader = PdfReader(file_path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


@shared_task(name="tasks.resume_tasks.process_resume_task")
def process_resume_task(candidate_id: int) -> dict:
    """Parse uploaded resume and persist extracted text for a candidate."""
    candidate = Candidate.query.get(candidate_id)
    if not candidate:
        return {"status": "not_found", "candidate_id": candidate_id}

    try:
        extracted_text = _extract_pdf_text(candidate.file_path)
        candidate.raw_text = extracted_text
        candidate.status = "processed"
        db.session.commit()
        return {
            "status": "processed",
            "candidate_id": candidate_id,
            "chars": len(extracted_text),
        }
    except Exception as exc:
        candidate.status = "failed"
        db.session.commit()
        return {
            "status": "failed",
            "candidate_id": candidate_id,
            "error": str(exc),
        }
