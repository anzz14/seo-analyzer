from datetime import datetime, timedelta, timezone
import uuid

import pytest
from httpx import AsyncClient
from jose import jwt

from app.config import settings


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient) -> None:
    email = f"register-{uuid.uuid4().hex}@example.com"
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    email = f"dup-{uuid.uuid4().hex}@example.com"
    payload = {"email": email, "password": "password123"}

    first = await client.post("/api/v1/auth/register", json=payload)
    second = await client.post("/api/v1/auth/register", json=payload)

    assert first.status_code == 201
    assert second.status_code == 400


@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": f"short-{uuid.uuid4().hex}@example.com", "password": "short"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "notanemail", "password": "password123"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    email = f"login-{uuid.uuid4().hex}@example.com"
    password = "password123"
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})

    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    email = f"wrong-{uuid.uuid4().hex}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "wrongpassword"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": f"unknown-{uuid.uuid4().hex}@example.com", "password": "password123"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_no_token(client: AsyncClient) -> None:
    response = await client.get("/api/v1/me")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_expired_token(client: AsyncClient) -> None:
    expired_token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "email": "expired@example.com",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    response = await client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401
