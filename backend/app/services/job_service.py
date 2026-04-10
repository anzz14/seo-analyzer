from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.processing_job import ProcessingJob


async def get_job(db: AsyncSession, job_id: str) -> ProcessingJob | None:
    try:
        parsed_id = uuid.UUID(job_id)
    except ValueError:
        return None

    return await db.get(ProcessingJob, parsed_id)
