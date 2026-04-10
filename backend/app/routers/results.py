from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.extracted_result import ExtractedResult
from app.models.user import User
from app.schemas.result import ExtractedResultResponse, PatchResultRequest
from app.services import result_service

router = APIRouter(tags=["results"], dependencies=[Depends(get_current_user)])


def _to_result_response(result: ExtractedResult) -> ExtractedResultResponse:
    return ExtractedResultResponse(
        id=str(result.id),
        document_id=str(result.document_id),
        job_id=str(result.job_id),
        word_count=result.word_count,
        readability_score=result.readability_score,
        primary_keywords=result.primary_keywords,
        auto_summary=result.auto_summary,
        user_edited_summary=result.user_edited_summary,
        is_finalized=result.is_finalized,
        finalized_at=result.finalized_at,
        created_at=result.created_at,
    )


@router.patch("/documents/{document_id}/result", response_model=ExtractedResultResponse)
async def patch_result(
    document_id: str,
    payload: PatchResultRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExtractedResultResponse:
    result = await result_service.patch_user_summary(
        db,
        document_id=document_id,
        user_id=current_user.id,
        new_summary=payload.user_edited_summary,
    )
    return _to_result_response(result)


@router.post("/documents/{document_id}/finalize", response_model=ExtractedResultResponse)
async def finalize_result(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExtractedResultResponse:
    result = await result_service.finalize_result(
        db,
        document_id=document_id,
        user_id=current_user.id,
    )
    return _to_result_response(result)
