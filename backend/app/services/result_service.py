from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.extracted_result import ExtractedResult
from app.models.processing_job import ProcessingJob


async def _get_owned_document(
    db: AsyncSession,
    document_id: str | UUID,
    user_id: str | UUID,
) -> Document:
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == user_id)
    )
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


async def get_result_by_document(
    db: AsyncSession,
    document_id: str | UUID,
) -> ExtractedResult | None:
    result = await db.execute(
        select(ExtractedResult).where(ExtractedResult.document_id == document_id)
    )
    return result.scalar_one_or_none()


async def patch_user_summary(
    db: AsyncSession,
    document_id: str | UUID,
    user_id: str | UUID,
    new_summary: str,
) -> ExtractedResult:
    """Update user_edited_summary for a document result.

    Args:
        db: Async database session.
        document_id: UUID of the document.
        user_id: UUID of the owner.
        new_summary: New summary text.

    Returns:
        Updated ExtractedResult.

    Raises:
        HTTPException: 404 if document/result not found; 409 if finalized.
    """


async def finalize_result(
    db: AsyncSession,
    document_id: str | UUID,
    user_id: str | UUID,
) -> ExtractedResult:
    """Mark result as finalized and prevent further user edits.

    Validates: document ownership, result exists, job is not stale (latest
    job_id matches result.job_id). Stale job indicates a retry was run
    after finalization was initiated — user must retry before re-finalizing.

    Args:
        db: Async database session.
        document_id: UUID of the document to finalize.
        user_id: UUID of the owner (used to verify authorization).

    Returns:
        Updated ExtractedResult with is_finalized=True and finalized_at set.

    Raises:
        HTTPException: 404 if document/result/job not found; 409 if already
            finalized or job is stale; 400 if latest_job_id != result.job_id.
    """
    document = await _get_owned_document(db, document_id, user_id)

    latest_job_result = await db.execute(
        select(ProcessingJob)
        .where(ProcessingJob.document_id == document.id)
        .order_by(ProcessingJob.created_at.desc(), ProcessingJob.id.desc())
        .limit(1)
    )
    latest_job = latest_job_result.scalar_one_or_none()
    if latest_job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    result = await get_result_by_document(db, document.id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result not found")

    if result.is_finalized:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already finalized")

    if latest_job.id != result.job_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stale job — retry analysis first",
        )

    result.is_finalized = True
    result.finalized_at = datetime.now(timezone.utc)
    latest_job.status = "finalized"

    await db.commit()
    await db.refresh(result)
    return result
