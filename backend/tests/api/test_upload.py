import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.processing_job import ProcessingJob


@pytest.mark.asyncio
async def test_upload_single_txt(
    client: AsyncClient,
    auth_headers: dict[str, str],
    sample_txt_file: tuple[str, tuple[str, bytes, str]],
) -> None:
    response = await client.post(
        "/api/v1/documents/upload",
        files=[sample_txt_file],
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert "document_id" in data[0]
    assert "job_id" in data[0]

    uuid.UUID(data[0]["document_id"])
    uuid.UUID(data[0]["job_id"])


@pytest.mark.asyncio
async def test_upload_multiple_txt(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    file_one = ("files", ("one.txt", b"first file", "text/plain"))
    file_two = ("files", ("two.txt", b"second file", "text/plain"))

    response = await client.post(
        "/api/v1/documents/upload",
        files=[file_one, file_two],
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


@pytest.mark.asyncio
async def test_upload_pdf_rejected(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    pdf_file = ("files", ("doc.pdf", b"%PDF-1.4", "application/pdf"))

    response = await client.post(
        "/api/v1/documents/upload",
        files=[pdf_file],
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_upload_too_large(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    large_content = b"a" * (6 * 1024 * 1024)
    huge_file = ("files", ("huge.txt", large_content, "text/plain"))

    response = await client.post(
        "/api/v1/documents/upload",
        files=[huge_file],
        headers=auth_headers,
    )

    assert response.status_code == 413


@pytest.mark.asyncio
async def test_upload_no_auth(
    client: AsyncClient,
    sample_txt_file: tuple[str, tuple[str, bytes, str]],
) -> None:
    response = await client.post("/api/v1/documents/upload", files=[sample_txt_file])

    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_upload_creates_job(
    client: AsyncClient,
    auth_headers: dict[str, str],
    sample_txt_file: tuple[str, tuple[str, bytes, str]],
    test_db: AsyncSession,
) -> None:
    response = await client.post(
        "/api/v1/documents/upload",
        files=[sample_txt_file],
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    job_id = data[0]["job_id"]

    job = await test_db.scalar(select(ProcessingJob).where(ProcessingJob.id == job_id))

    assert job is not None
    assert job.status == "queued"
