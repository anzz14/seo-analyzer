from __future__ import annotations

from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.extracted_result import ExtractedResult
from app.models.processing_job import ProcessingJob


async def _seed_completed_result(
    test_db: AsyncSession,
    document_id: str,
    job_id: str,
    *,
    finalized: bool = False,
) -> None:
    job = await test_db.scalar(select(ProcessingJob).where(ProcessingJob.id == job_id))
    assert job is not None

    job.status = "completed"
    job.progress_percentage = 100
    job.completed_at = datetime.now(timezone.utc)

    extracted = ExtractedResult(
        document_id=document_id,
        job_id=job.id,
        word_count=120,
        readability_score=72.4,
        primary_keywords=[{"keyword": "seo", "count": 6, "density": 5.0}],
        auto_summary="Initial auto summary",
        user_edited_summary=None,
        is_finalized=finalized,
        finalized_at=datetime.now(timezone.utc) if finalized else None,
    )
    test_db.add(extracted)
    await test_db.flush()


@pytest.mark.asyncio
async def test_patch_summary(
    client: AsyncClient,
    auth_headers: dict[str, str],
    create_document_for_user,
    test_db: AsyncSession,
) -> None:
    upload = await create_document_for_user(auth_headers)
    await _seed_completed_result(test_db, upload["document_id"], upload["job_id"])

    response = await client.patch(
        f"/api/v1/documents/{upload['document_id']}/result",
        headers=auth_headers,
        json={"user_edited_summary": "Manually tuned summary"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user_edited_summary"] == "Manually tuned summary"


@pytest.mark.asyncio
async def test_patch_summary_no_result(
    client: AsyncClient,
    auth_headers: dict[str, str],
    create_document_for_user,
) -> None:
    upload = await create_document_for_user(auth_headers)

    response = await client.patch(
        f"/api/v1/documents/{upload['document_id']}/result",
        headers=auth_headers,
        json={"user_edited_summary": "Draft summary"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_patch_summary_wrong_user(
    client: AsyncClient,
    auth_headers: dict[str, str],
    second_user_auth_headers: dict[str, str],
    create_document_for_user,
    test_db: AsyncSession,
) -> None:
    upload_other = await create_document_for_user(second_user_auth_headers)
    await _seed_completed_result(test_db, upload_other["document_id"], upload_other["job_id"])

    response = await client.patch(
        f"/api/v1/documents/{upload_other['document_id']}/result",
        headers=auth_headers,
        json={"user_edited_summary": "Unauthorized update"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_patch_summary_after_finalize(
    client: AsyncClient,
    auth_headers: dict[str, str],
    create_document_for_user,
    test_db: AsyncSession,
) -> None:
    upload = await create_document_for_user(auth_headers)
    await _seed_completed_result(
        test_db,
        upload["document_id"],
        upload["job_id"],
        finalized=True,
    )

    response = await client.patch(
        f"/api/v1/documents/{upload['document_id']}/result",
        headers=auth_headers,
        json={"user_edited_summary": "Should fail"},
    )

    assert response.status_code == 409
