from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
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


@router.get("", response_model=list[UploadResponse])
async def list_documents_stub() -> list[UploadResponse]:
    return []
