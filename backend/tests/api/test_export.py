from __future__ import annotations

import csv
from datetime import datetime, timezone
from io import StringIO

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.extracted_result import ExtractedResult
from app.models.processing_job import ProcessingJob


async def _seed_result(
    test_db: AsyncSession,
    document_id: str,
    job_id: str,
    *,
    finalized: bool,
) -> None:
    job = await test_db.scalar(select(ProcessingJob).where(ProcessingJob.id == job_id))
    assert job is not None

    job.status = "finalized" if finalized else "completed"
    job.progress_percentage = 100
    job.completed_at = datetime.now(timezone.utc)

    extracted = ExtractedResult(
        document_id=document_id,
        job_id=job.id,
        word_count=140,
        readability_score=61.25,
        primary_keywords=[{"keyword": "seo", "count": 7, "density": 5.0}],
        auto_summary="Generated summary",
        user_edited_summary="Edited summary" if finalized else None,
        is_finalized=finalized,
        finalized_at=datetime.now(timezone.utc) if finalized else None,
    )
    test_db.add(extracted)
    await test_db.flush()


@pytest.mark.asyncio
async def test_export_json_finalized(
    client: AsyncClient,
    auth_headers: dict[str, str],
    create_document_for_user,
    test_db: AsyncSession,
) -> None:
    upload = await create_document_for_user(auth_headers)
    await _seed_result(test_db, upload["document_id"], upload["job_id"], finalized=True)

    response = await client.get(
        f"/api/v1/documents/{upload['document_id']}/export?format=json",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")

    data = response.json()
    assert "word_count" in data
    assert "readability_score" in data
    assert "primary_keywords" in data
    assert "auto_summary" in data


@pytest.mark.asyncio
async def test_export_csv_finalized(
    client: AsyncClient,
    auth_headers: dict[str, str],
    create_document_for_user,
    test_db: AsyncSession,
) -> None:
    upload = await create_document_for_user(auth_headers)
    await _seed_result(test_db, upload["document_id"], upload["job_id"], finalized=True)

    response = await client.get(
        f"/api/v1/documents/{upload['document_id']}/export?format=csv",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")

    rows = list(csv.reader(StringIO(response.text)))
    assert len(rows) == 2
    header = rows[0]
    header[0] = header[0].lstrip("\ufeff")
    assert header == [
        "document_id",
        "filename",
        "word_count",
        "readability_score",
        "primary_keywords",
        "auto_content",
        "user_edited_content",
        "finalized_at",
    ]


@pytest.mark.asyncio
async def test_export_not_finalized(
    client: AsyncClient,
    auth_headers: dict[str, str],
    create_document_for_user,
    test_db: AsyncSession,
) -> None:
    upload = await create_document_for_user(auth_headers)
    await _seed_result(test_db, upload["document_id"], upload["job_id"], finalized=False)

    response = await client.get(
        f"/api/v1/documents/{upload['document_id']}/export?format=json",
        headers=auth_headers,
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_export_wrong_user(
    client: AsyncClient,
    auth_headers: dict[str, str],
    second_user_auth_headers: dict[str, str],
    create_document_for_user,
    test_db: AsyncSession,
) -> None:
    upload_other = await create_document_for_user(second_user_auth_headers)
    await _seed_result(test_db, upload_other["document_id"], upload_other["job_id"], finalized=True)

    response = await client.get(
        f"/api/v1/documents/{upload_other['document_id']}/export?format=json",
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_bulk_export_csv(
    client: AsyncClient,
    auth_headers: dict[str, str],
    create_document_for_user,
    test_db: AsyncSession,
) -> None:
    uploads = [await create_document_for_user(auth_headers) for _ in range(3)]
    for upload in uploads:
        await _seed_result(test_db, upload["document_id"], upload["job_id"], finalized=True)

    response = await client.get("/api/v1/export/bulk?format=csv", headers=auth_headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")

    rows = list(csv.reader(StringIO(response.text)))
    assert len(rows) == 4


@pytest.mark.asyncio
async def test_bulk_export_excludes_other_users(
    client: AsyncClient,
    auth_headers: dict[str, str],
    second_user_auth_headers: dict[str, str],
    create_document_for_user,
    test_db: AsyncSession,
) -> None:
    own_upload = await create_document_for_user(auth_headers)
    other_upload = await create_document_for_user(second_user_auth_headers)

    await _seed_result(test_db, own_upload["document_id"], own_upload["job_id"], finalized=True)
    await _seed_result(test_db, other_upload["document_id"], other_upload["job_id"], finalized=True)

    response = await client.get("/api/v1/export/bulk?format=csv", headers=auth_headers)

    assert response.status_code == 200
    rows = list(csv.reader(StringIO(response.text)))

    own_ids = {row[0] for row in rows[1:]}
    assert own_upload["document_id"] in own_ids
    assert other_upload["document_id"] not in own_ids
