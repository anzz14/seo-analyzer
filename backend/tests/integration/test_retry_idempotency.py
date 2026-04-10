from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.database import SyncSession
from app.models.document import Document
from app.models.extracted_result import ExtractedResult
from app.models.processing_job import ProcessingJob
from app.models.user import User
from app.workers.tasks import analyze_document


def _seed_document_and_job(file_path: Path) -> tuple[uuid.UUID, uuid.UUID]:
    with SyncSession() as db:
        user = User(email=f"retry-{uuid.uuid4().hex}@example.com", hashed_password="hashed-password")
        db.add(user)
        db.flush()

        document = Document(
            user_id=user.id,
            original_filename="retry.txt",
            file_path=str(file_path),
            file_size=0,
            mime_type="text/plain",
            upload_timestamp=datetime.now(timezone.utc),
        )
        db.add(document)
        db.flush()

        job = ProcessingJob(document_id=document.id, status="queued")
        db.add(job)
        db.commit()

        return document.id, job.id


def _create_retry_job(document_id: uuid.UUID) -> uuid.UUID:
    with SyncSession() as db:
        retry_job = ProcessingJob(document_id=document_id, status="queued")
        db.add(retry_job)
        db.commit()
        return retry_job.id


def test_retry_upsert_is_idempotent_and_preserves_user_edit(tmp_path: Path) -> None:
    file_path = tmp_path / "retry-content.txt"
    file_path.write_text(
        "SEO copy should remain consistent. This sentence repeats SEO value for analysis.",
        encoding="utf-8",
    )

    document_id, first_job_id = _seed_document_and_job(file_path)

    first = analyze_document.apply(args=[str(first_job_id), str(document_id), str(file_path)])
    assert first.failed() is False

    with SyncSession() as db:
        initial_rows = db.query(ExtractedResult).filter(ExtractedResult.document_id == document_id).all()
        assert len(initial_rows) == 1
        initial_rows[0].user_edited_summary = "User approved edited summary"
        db.commit()

    second_job_id = _create_retry_job(document_id)
    second = analyze_document.apply(args=[str(second_job_id), str(document_id), str(file_path)])
    assert second.failed() is False

    with SyncSession() as db:
        final_rows = db.query(ExtractedResult).filter(ExtractedResult.document_id == document_id).all()
        assert len(final_rows) == 1
        assert final_rows[0].user_edited_summary == "User approved edited summary"
