from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.database import SyncSession
from app.models.document import Document
from app.models.extracted_result import ExtractedResult
from app.models.processing_job import ProcessingJob
from app.models.user import User
from app.workers.tasks import analyze_document


@pytest.fixture
def seeded_job(tmp_path: Path) -> tuple[uuid.UUID, uuid.UUID]:
    user_email = f"worker-{uuid.uuid4().hex}@example.com"

    with SyncSession() as db:
        user = User(email=user_email, hashed_password="hashed-password")
        db.add(user)
        db.flush()

        document = Document(
            user_id=user.id,
            original_filename="input.txt",
            file_path=str(tmp_path / "input.txt"),
            file_size=0,
            mime_type="text/plain",
            upload_timestamp=datetime.now(timezone.utc),
        )
        db.add(document)
        db.flush()

        job = ProcessingJob(document_id=document.id, status="queued")
        db.add(job)
        db.commit()

        return job.id, document.id


def test_pipeline_success(tmp_path: Path, seeded_job: tuple[uuid.UUID, uuid.UUID]) -> None:
    job_id, document_id = seeded_job
    tmp_file_path = tmp_path / "known-content.txt"
    tmp_file_path.write_text(
        "SEO analysis helps teams improve rankings. This is easy to read and short.",
        encoding="utf-8",
    )

    result = analyze_document.apply(args=[str(job_id), str(document_id), str(tmp_file_path)])
    assert result.failed() is False

    with SyncSession() as db:
        job = db.get(ProcessingJob, job_id)
        assert job is not None
        assert job.status == "completed"
        assert job.progress_percentage == 100
        assert job.completed_at is not None

        extracted = db.query(ExtractedResult).filter(ExtractedResult.document_id == document_id).one_or_none()
        assert extracted is not None
        assert extracted.word_count is not None and extracted.word_count > 0
        assert extracted.readability_score is not None
        assert 0 <= extracted.readability_score <= 100
        assert isinstance(extracted.primary_keywords, list)
        assert len(extracted.primary_keywords) > 0
        assert extracted.auto_summary is not None
        assert len(extracted.auto_summary) > 0


def test_pipeline_file_not_found(seeded_job: tuple[uuid.UUID, uuid.UUID]) -> None:
    job_id, document_id = seeded_job

    result = analyze_document.apply(args=[str(job_id), str(document_id), "/nonexistent/path.txt"])
    assert result.failed() is False

    with SyncSession() as db:
        job = db.get(ProcessingJob, job_id)
        assert job is not None
        assert job.status == "failed"
        assert job.error_message is not None
