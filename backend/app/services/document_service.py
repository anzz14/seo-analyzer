from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import Select, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.document import Document
from app.models.processing_job import ProcessingJob


async def create_document(
    db: AsyncSession,
    user_id: str | UUID,
    filename: str,
    file_path: str,
    file_size: int,
    mime_type: str,
) -> Document:
    document = Document(
        user_id=user_id,
        original_filename=filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=mime_type,
        upload_timestamp=datetime.utcnow(),
    )
    db.add(document)
    await db.flush()
    await db.refresh(document)
    return document


async def create_job_for_document(db: AsyncSession, document_id: str | UUID) -> ProcessingJob:
    job = ProcessingJob(document_id=document_id, status="queued")
    db.add(job)
    await db.flush()
    await db.refresh(job)
    return job


def _latest_job_subquery():
    return (
        select(
            ProcessingJob.id.label("job_id"),
            ProcessingJob.document_id.label("document_id"),
            ProcessingJob.status.label("status"),
            func.row_number()
            .over(
                partition_by=ProcessingJob.document_id,
                order_by=(ProcessingJob.created_at.desc(), ProcessingJob.id.desc()),
            )
            .label("rn"),
        )
        .subquery("latest_job")
    )


def _get_sort_column(sort_by: str):
    if sort_by == "filename":
        return Document.original_filename
    return Document.created_at


def _get_sort_clause(sort_by: str, sort_order: str):
    column = _get_sort_column(sort_by)
    if sort_order.lower() == "asc":
        return asc(column)
    return desc(column)


def _apply_document_filters(
    query: Select,
    user_id: str | UUID,
    status_filter: str | None,
    search: str | None,
):
    query = query.where(Document.user_id == user_id)

    if search:
        query = query.where(Document.original_filename.ilike(f"%{search}%"))

    if status_filter:
        latest_job = _latest_job_subquery()
        query = query.join(
            latest_job,
            (latest_job.c.document_id == Document.id) & (latest_job.c.rn == 1),
        ).where(latest_job.c.status == status_filter)

    return query


async def list_documents(
    db: AsyncSession,
    user_id: str | UUID,
    page: int,
    page_size: int,
    status_filter: str | None,
    search: str | None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> tuple[list[Document], int]:
    page = max(page, 1)
    page_size = max(page_size, 1)

    latest_job = _latest_job_subquery()

    base_docs_query = _apply_document_filters(
        select(Document),
        user_id=user_id,
        status_filter=status_filter,
        search=search,
    )

    count_query = _apply_document_filters(
        select(func.count()).select_from(Document),
        user_id=user_id,
        status_filter=status_filter,
        search=search,
    )

    rows_result = await db.execute(
        base_docs_query
        .order_by(_get_sort_clause(sort_by, sort_order))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = list(rows_result.scalars().all())

    total_result = await db.execute(count_query)
    total_count = int(total_result.scalar_one() or 0)

    if not rows:
        return rows, total_count

    doc_ids = [doc.id for doc in rows]
    latest_jobs_result = await db.execute(
        select(ProcessingJob)
        .join(latest_job, ProcessingJob.id == latest_job.c.job_id)
        .where(latest_job.c.rn == 1, ProcessingJob.document_id.in_(doc_ids))
    )
    latest_jobs_map = {job.document_id: job for job in latest_jobs_result.scalars().all()}

    for doc in rows:
        setattr(doc, "latest_job", latest_jobs_map.get(doc.id))

    return rows, total_count


async def get_document(db: AsyncSession, document_id: str | UUID, user_id: str | UUID) -> Document:
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == user_id)
    )
    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document


async def get_document_no_auth_check(
    db: AsyncSession,
    document_id: str | UUID,
) -> Document | None:
    result = await db.execute(select(Document).where(Document.id == document_id))
    return result.scalar_one_or_none()


async def get_document_with_details(
    db: AsyncSession, doc_id: str | UUID, user_id: str | UUID
) -> Document:
    result = await db.execute(
        select(Document)
        .options(
            joinedload(Document.processing_jobs),
            joinedload(Document.extracted_result),
        )
        .where(Document.id == doc_id, Document.user_id == user_id)
    )
    document = result.unique().scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    latest_job = None
    if document.processing_jobs:
        latest_job = sorted(
            document.processing_jobs,
            key=lambda job: (job.created_at or datetime.min.replace(tzinfo=timezone.utc), job.id),
            reverse=True,
        )[0]
    setattr(document, "latest_job", latest_job)

    return document
