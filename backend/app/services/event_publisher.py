import asyncio  # noqa: F401
import json
import logging

import redis as sync_redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings

logger = logging.getLogger(__name__)

_redis_client = sync_redis.from_url(settings.REDIS_URL)


def publish_and_persist(
    db_session_sync: Session,
    job_id: str,
    stage: str,
    percentage: int,
    message: str,
) -> None:
    db_session_sync.execute(
        text(
            """
            UPDATE processing_jobs
            SET progress_percentage = :pct,
                current_stage = :stage
            WHERE id = :job_id
            """
        ),
        {
            "pct": percentage,
            "stage": stage,
            "job_id": job_id,
        },
    )
    db_session_sync.commit()

    payload = json.dumps(
        {
            "stage": stage,
            "percentage": percentage,
            "message": message,
            "job_id": job_id,
        }
    )

    try:
        _redis_client.publish(f"job_progress:{job_id}", payload)
    except sync_redis.exceptions.ConnectionError:
        logger.exception("Redis publish failed for job_id=%s", job_id)
