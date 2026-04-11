from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis import asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.job import JobResponse
from app.services import document_service, job_service
from app.services.auth_service import decode_token

router = APIRouter(prefix="/jobs", tags=["jobs"])
security = HTTPBearer(auto_error=False)


@router.post("/{job_id}/retry", response_model=JobResponse)
async def retry_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobResponse:
    job = await job_service.reset_job_for_retry(db, job_id, str(current_user.id))

    return JobResponse(
        id=str(job.id),
        document_id=str(job.document_id),
        status=job.status,
        progress_percentage=job.progress_percentage,
        current_stage=job.current_stage,
        error_message=job.error_message,
        retry_count=job.retry_count,
        celery_task_id=job.celery_task_id,
        started_at=job.started_at,
        completed_at=job.completed_at,
        created_at=job.created_at,
    )


async def _resolve_current_user(
    db: AsyncSession,
    credentials: HTTPAuthorizationCredentials | None,
    token: str | None,
) -> User:
    if credentials is not None:
        token_value = credentials.credentials
    elif token:
        token_value = token
    else:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_token(token_value)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return user


@router.get("/{job_id}/progress/stream")
async def stream_progress(
    job_id: str,
    token: str | None = Query(None),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    current_user = await _resolve_current_user(db, credentials, token)

    job = await job_service.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    doc = await document_service.get_document_no_auth_check(db, job.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if str(doc.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status in ("completed", "failed", "finalized"):
        stage = "job_completed" if job.status in ("completed", "finalized") else "job_failed"
        data = json.dumps(
            {
                "stage": stage,
                "percentage": job.progress_percentage,
                "job_id": job_id,
            }
        )

        async def quick_stream():
            yield f"data: {data}\n\n"

        return StreamingResponse(quick_stream(), media_type="text/event-stream")

    async def live_stream():
        channel = f"job_progress:{job_id}"
        redis_conn = aioredis.from_url(settings.REDIS_URL)
        pubsub = redis_conn.pubsub()
        await pubsub.subscribe(channel)

        try:
            async for message in pubsub.listen():
                if message.get("type") != "message":
                    continue

                raw_data = message.get("data")
                if isinstance(raw_data, bytes):
                    payload_str = raw_data.decode()
                else:
                    payload_str = str(raw_data)

                yield f"data: {payload_str}\n\n"

                try:
                    parsed = json.loads(payload_str)
                except json.JSONDecodeError:
                    continue

                if parsed.get("stage") in ("job_completed", "job_failed"):
                    break
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
            await redis_conn.aclose()

    return StreamingResponse(
        live_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
