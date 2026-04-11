from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.processing_job import ProcessingJob
from app.workers.tasks import analyze_document


async def get_job(db: AsyncSession, job_id: str) -> ProcessingJob | None:
    try:
        parsed_id = uuid.UUID(job_id)
    except ValueError:
        return None

    return await db.get(ProcessingJob, parsed_id)


async def reset_job_for_retry(
    db: AsyncSession,
    job_id: str,
    user_id: str,
) -> ProcessingJob:
    """Reset a failed job to queued state and dispatch retry task.

    Validates: job exists, belongs to user, status is 'failed'. Resets state:
    queued, 0% progress, clears error_message, increments retry_count,
    clears celery_task_id and timestamps. Dispatches new Celery task.

    Args:
        db: Async database session.
        job_id: UUID string of the job to retry (validated as UUID).
        user_id: UUID string to verify job ownership via document.

    Returns:
        Updated ProcessingJob with new celery_task_id and reset state.

    Raises:
        HTTPException: 404 if job/document not found or invalid UUID;
            400 if job status is not 'failed'.
    """
    try:
        parsed_id = uuid.UUID(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found") from exc

    query = (
        select(ProcessingJob, Document)
        .join(Document, Document.id == ProcessingJob.document_id)
        .where(ProcessingJob.id == parsed_id, Document.user_id == user_id)
    )
    row = (await db.execute(query)).one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    job, document = row

    if job.status not in ("failed",):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only retry failed jobs",
        )

    job.status = "queued"
    job.progress_percentage = 0
    job.current_stage = "job_queued"
    job.error_message = None
    job.retry_count = (job.retry_count or 0) + 1
    job.celery_task_id = None
    job.started_at = None
    job.completed_at = None

    new_task = analyze_document.delay(str(job.id), str(document.id), document.file_path)
    job.celery_task_id = str(new_task.id)

    await db.commit()
    await db.refresh(job)
    return job
