from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import delete, select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.document import Document
from app.models.extracted_result import ExtractedResult
from app.models.processing_job import ProcessingJob
from app.models.user import User
from app.services.auth_service import hash_password

SEED_EMAIL = "seed.user@example.com"
SEED_PASSWORD = "SeedPass123!"


async def _get_or_create_seed_user(db) -> User:
    user = await db.scalar(select(User).where(User.email == SEED_EMAIL))
    if user is None:
        user = User(email=SEED_EMAIL, hashed_password=hash_password(SEED_PASSWORD), is_active=True)
        db.add(user)
        await db.flush()
    else:
        # Keep credentials predictable for local testing.
        user.hashed_password = hash_password(SEED_PASSWORD)
        user.is_active = True

    await db.refresh(user)
    return user


async def _clear_existing_seed_documents(db, user_id) -> None:
    doc_ids = list((await db.scalars(select(Document.id).where(Document.user_id == user_id))).all())
    if not doc_ids:
        return

    await db.execute(delete(ExtractedResult).where(ExtractedResult.document_id.in_(doc_ids)))
    await db.execute(delete(ProcessingJob).where(ProcessingJob.document_id.in_(doc_ids)))
    await db.execute(delete(Document).where(Document.id.in_(doc_ids)))
    await db.flush()


def _write_seed_file(path: Path, content: str) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = content.encode("utf-8")
    path.write_bytes(payload)
    return len(payload)


async def seed() -> None:
    upload_root = Path(settings.UPLOAD_DIR)

    async with AsyncSessionLocal() as db:
        user = await _get_or_create_seed_user(db)
        await _clear_existing_seed_documents(db, user.id)

        seed_dir = upload_root / str(user.id)

        now = datetime.now(timezone.utc)

        finalized_path = seed_dir / "seed_finalized.txt"
        processing_path = seed_dir / "seed_processing.txt"
        failed_path = seed_dir / "seed_failed.txt"

        finalized_size = _write_seed_file(
            finalized_path,
            "SEO content planning helps teams improve clarity and consistency across channels.",
        )
        processing_size = _write_seed_file(
            processing_path,
            "This document is marked as processing for dashboard testing.",
        )
        failed_size = _write_seed_file(
            failed_path,
            "This document is marked as failed so retry can be tested.",
        )

        doc_finalized = Document(
            user_id=user.id,
            original_filename="seed_finalized.txt",
            file_path=str(finalized_path),
            file_size=finalized_size,
            mime_type="text/plain",
            upload_timestamp=now,
        )
        doc_processing = Document(
            user_id=user.id,
            original_filename="seed_processing.txt",
            file_path=str(processing_path),
            file_size=processing_size,
            mime_type="text/plain",
            upload_timestamp=now,
        )
        doc_failed = Document(
            user_id=user.id,
            original_filename="seed_failed.txt",
            file_path=str(failed_path),
            file_size=failed_size,
            mime_type="text/plain",
            upload_timestamp=now,
        )

        db.add_all([doc_finalized, doc_processing, doc_failed])
        await db.flush()

        job_finalized = ProcessingJob(
            document_id=doc_finalized.id,
            status="finalized",
            progress_percentage=100,
            current_stage="job_completed",
            retry_count=0,
            started_at=now,
            completed_at=now,
        )
        job_processing = ProcessingJob(
            document_id=doc_processing.id,
            status="processing",
            progress_percentage=35,
            current_stage="analyzing",
            retry_count=0,
            started_at=now,
            completed_at=None,
        )
        job_failed = ProcessingJob(
            document_id=doc_failed.id,
            status="failed",
            progress_percentage=0,
            current_stage="job_failed",
            error_message="Seeded failure for retry testing",
            retry_count=1,
            started_at=now,
            completed_at=now,
        )

        db.add_all([job_finalized, job_processing, job_failed])
        await db.flush()

        result_finalized = ExtractedResult(
            document_id=doc_finalized.id,
            job_id=job_finalized.id,
            word_count=45,
            readability_score=67.8,
            primary_keywords=[
                {"keyword": "seo", "count": 3, "density": 6.7},
                {"keyword": "content", "count": 2, "density": 4.4},
            ],
            auto_summary="Seeded finalized summary for export and review tests.",
            user_edited_summary="Seeded user-edited summary.",
            is_finalized=True,
            finalized_at=now,
        )
        db.add(result_finalized)

        await db.commit()

    print("Seed complete")
    print(f"Login email: {SEED_EMAIL}")
    print(f"Login password: {SEED_PASSWORD}")
    print("Inserted documents: 3")


if __name__ == "__main__":
    asyncio.run(seed())
