from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.processing_job import ProcessingJob


async def _set_job_status(
    test_db: AsyncSession,
    job_id: str,
    status: str,
    celery_task_id: str | None = None,
) -> None:
    job = await test_db.scalar(select(ProcessingJob).where(ProcessingJob.id == job_id))
    assert job is not None
    job.status = status
    if celery_task_id is not None:
        job.celery_task_id = celery_task_id
    await test_db.flush()


@pytest.mark.asyncio
async def test_retry_failed_job(
    client: AsyncClient,
    auth_headers: dict[str, str],
    create_document_for_user,
    test_db: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    upload = await create_document_for_user(auth_headers)
    await _set_job_status(test_db, upload["job_id"], "failed", celery_task_id="old-task")

    monkeypatch.setattr(
        "app.services.job_service.analyze_document",
        SimpleNamespace(delay=lambda *_args, **_kwargs: SimpleNamespace(id="new-task-id")),
    )

    response = await client.post(f"/api/v1/jobs/{upload['job_id']}/retry", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    assert data["error_message"] is None


@pytest.mark.asyncio
async def test_retry_completed_job(
    client: AsyncClient,
    auth_headers: dict[str, str],
    create_document_for_user,
    test_db: AsyncSession,
) -> None:
    upload = await create_document_for_user(auth_headers)
    await _set_job_status(test_db, upload["job_id"], "completed")

    response = await client.post(f"/api/v1/jobs/{upload['job_id']}/retry", headers=auth_headers)

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_retry_processing_job(
    client: AsyncClient,
    auth_headers: dict[str, str],
    create_document_for_user,
    test_db: AsyncSession,
) -> None:
    upload = await create_document_for_user(auth_headers)
    await _set_job_status(test_db, upload["job_id"], "processing")

    response = await client.post(f"/api/v1/jobs/{upload['job_id']}/retry", headers=auth_headers)

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_retry_other_users_job(
    client: AsyncClient,
    auth_headers: dict[str, str],
    second_user_auth_headers: dict[str, str],
    create_document_for_user,
    test_db: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    upload_other = await create_document_for_user(second_user_auth_headers)
    await _set_job_status(test_db, upload_other["job_id"], "failed")

    monkeypatch.setattr(
        "app.services.job_service.analyze_document",
        SimpleNamespace(delay=lambda *_args, **_kwargs: SimpleNamespace(id="new-task-id")),
    )

    response = await client.post(
        f"/api/v1/jobs/{upload_other['job_id']}/retry",
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_retry_changes_celery_task_id(
    client: AsyncClient,
    auth_headers: dict[str, str],
    create_document_for_user,
    test_db: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    upload = await create_document_for_user(auth_headers)
    old_task_id = f"old-{uuid.uuid4().hex}"
    await _set_job_status(test_db, upload["job_id"], "failed", celery_task_id=old_task_id)

    new_task_id = f"new-{uuid.uuid4().hex}"
    monkeypatch.setattr(
        "app.services.job_service.analyze_document",
        SimpleNamespace(delay=lambda *_args, **_kwargs: SimpleNamespace(id=new_task_id)),
    )

    response = await client.post(f"/api/v1/jobs/{upload['job_id']}/retry", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["celery_task_id"] != old_task_id
    assert data["celery_task_id"] == new_task_id
