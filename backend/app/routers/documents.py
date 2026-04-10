from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.processing_job import ProcessingJob
from app.models.user import User
from app.schemas.document import DocumentListResponse, DocumentResponse
from app.schemas.job import JobResponse
from app.schemas.job import UploadResponse
from app.services import document_service

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/upload", response_model=list[UploadResponse], status_code=status.HTTP_201_CREATED)
async def upload_documents(
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[UploadResponse]:
    upload_dir = Path(settings.UPLOAD_DIR) / str(current_user.id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    results: list[UploadResponse] = []

    for file in files:
        if file.content_type != "text/plain":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Only .txt files allowed",
            )

        file_bytes = await file.read()
        file_size = len(file_bytes)

        if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File too large",
            )

        safe_filename = Path(file.filename or "upload.txt").name
        stored_filename = f"{uuid4()}_{safe_filename}"
        stored_path = upload_dir / stored_filename

        stored_path.write_bytes(file_bytes)

        document = await document_service.create_document(
            db=db,
            user_id=current_user.id,
            filename=safe_filename,
            file_path=str(stored_path),
            file_size=file_size,
            mime_type=file.content_type,
        )
        job = await document_service.create_job_for_document(db=db, document_id=document.id)

        # Lazy import avoids circular imports between routers/services and worker tasks.
        from app.workers.tasks import analyze_document

        analyze_document.delay(str(job.id), str(document.id), str(stored_path))

        results.append(
            UploadResponse(
                document_id=str(document.id),
                job_id=str(job.id),
                filename=safe_filename,
                file_size=file_size,
            )
        )

    return results


def _to_document_response(document, latest_job: ProcessingJob | None) -> DocumentResponse:
    latest_job_response: JobResponse | None = None
    if latest_job is not None:
        latest_job_response = JobResponse(
            id=str(latest_job.id),
            document_id=str(latest_job.document_id),
            status=latest_job.status,
            progress_percentage=latest_job.progress_percentage,
            current_stage=latest_job.current_stage,
            error_message=latest_job.error_message,
            retry_count=latest_job.retry_count,
            celery_task_id=latest_job.celery_task_id,
            started_at=latest_job.started_at,
            completed_at=latest_job.completed_at,
            created_at=latest_job.created_at,
        )

    return DocumentResponse(
        id=str(document.id),
        user_id=str(document.user_id),
        original_filename=document.original_filename,
        file_size=document.file_size,
        mime_type=document.mime_type,
        upload_timestamp=document.upload_timestamp,
        created_at=document.created_at,
        latest_job=latest_job_response,
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    search: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentListResponse:
    docs, total = await document_service.list_documents(
        db,
        current_user.id,
        page,
        page_size,
        status,
        search,
        sort_by,
        sort_order,
    )

    items: list[DocumentResponse] = []
    for doc in docs:
        latest_job = getattr(doc, "latest_job", None)
        items.append(_to_document_response(doc, latest_job))

    return DocumentListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentResponse:
    document = await document_service.get_document_with_details(db, document_id, current_user.id)
    latest_job = getattr(document, "latest_job", None)
    return _to_document_response(document, latest_job)
