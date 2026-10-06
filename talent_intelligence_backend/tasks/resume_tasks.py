from __future__ import annotations

from celery import shared_task
from PyPDF2 import PdfReader

from services.candidate_analysis import process_analysis


def _extract_pdf_text(file_path: str) -> str:
    reader = PdfReader(file_path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


@shared_task(name="tasks.resume_tasks.process_resume_task", acks_late=True, reject_on_worker_lost=True)
def process_resume_task(candidate_id: int) -> dict:
    """Persist provider outcomes independently of recruiter-controlled stages."""
    return process_analysis(candidate_id, _extract_pdf_text)
