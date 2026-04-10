from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.processing_job import ProcessingJob


@pytest.mark.asyncio
async def test_list_empty(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    response = await client.get("/api/v1/documents", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_returns_only_own(
    client: AsyncClient,
    auth_headers: dict[str, str],
    second_user_auth_headers: dict[str, str],
    create_document_for_user,
) -> None:
    for _ in range(3):
        await create_document_for_user(auth_headers)

    await create_document_for_user(second_user_auth_headers)

    response = await client.get("/api/v1/documents", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_list_pagination(
    client: AsyncClient,
    auth_headers: dict[str, str],
    create_document_for_user,
) -> None:
    for _ in range(5):
        await create_document_for_user(auth_headers)

    response = await client.get("/api/v1/documents?page=1&page_size=2", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2


@pytest.mark.asyncio
async def test_list_filter_by_status(
    client: AsyncClient,
    auth_headers: dict[str, str],
    create_document_for_user,
    test_db: AsyncSession,
) -> None:
    first_upload = await create_document_for_user(auth_headers)
    await create_document_for_user(auth_headers)

    first_job = await test_db.scalar(
        select(ProcessingJob).where(ProcessingJob.id == first_upload["job_id"])
    )
    assert first_job is not None
    first_job.status = "completed"
    first_job.current_stage = "finalized"
    await test_db.flush()

    response = await client.get("/api/v1/documents?status=completed", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["latest_job"]["status"] == "completed"


@pytest.mark.asyncio
async def test_list_search(
    client: AsyncClient,
    auth_headers: dict[str, str],
    create_document_for_user,
) -> None:
    await create_document_for_user(auth_headers, filename="unique_name.txt")

    response = await client.get("/api/v1/documents?search=unique", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(item["original_filename"] == "unique_name.txt" for item in data["items"])


@pytest.mark.asyncio
async def test_list_sort_desc(
    client: AsyncClient,
    auth_headers: dict[str, str],
    create_document_for_user,
) -> None:
    for _ in range(3):
        await create_document_for_user(auth_headers)

    response = await client.get(
        "/api/v1/documents?sort_by=created_at&sort_order=desc",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    created_times = [datetime.fromisoformat(item["created_at"]) for item in data["items"]]
    assert created_times == sorted(created_times, reverse=True)


@pytest.mark.asyncio
async def test_get_document_own(
    client: AsyncClient,
    auth_headers: dict[str, str],
    create_document_for_user,
) -> None:
    upload = await create_document_for_user(auth_headers)

    response = await client.get(f"/api/v1/documents/{upload['document_id']}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == upload["document_id"]


@pytest.mark.asyncio
async def test_get_document_other_user(
    client: AsyncClient,
    auth_headers: dict[str, str],
    second_user_auth_headers: dict[str, str],
    create_document_for_user,
) -> None:
    other_upload = await create_document_for_user(second_user_auth_headers)

    response = await client.get(
        f"/api/v1/documents/{other_upload['document_id']}",
        headers=auth_headers,
    )

    assert response.status_code == 404
