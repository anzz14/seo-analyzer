import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
from collections.abc import Awaitable, Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest_asyncio
from fastapi import Depends
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.database import Base, get_db
from app.dependencies.auth import get_current_user
from app.main import app
from app.models.user import User


@pytest_asyncio.fixture
async def test_db() -> AsyncSession:
	engine = create_async_engine(settings.DATABASE_URL)

	async with engine.connect() as connection:
		transaction = await connection.begin()

		# Ensure UUID default generation works in PostgreSQL test environments.
		await connection.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
		await connection.run_sync(Base.metadata.create_all)

		session_factory = async_sessionmaker(bind=connection, expire_on_commit=False)
		session = session_factory()
		try:
			yield session
		finally:
			await session.close()
			await transaction.rollback()

	await engine.dispose()


@pytest_asyncio.fixture
async def client(test_db: AsyncSession) -> AsyncClient:
	async def override_get_db() -> AsyncSession:
		yield test_db

	app.dependency_overrides[get_db] = override_get_db

	if not any(route.path == "/api/v1/me" for route in app.routes):

		@app.get("/api/v1/me")
		async def me(current_user: User = Depends(get_current_user)) -> dict[str, str]:
			return {"id": str(current_user.id), "email": current_user.email}

	transport = ASGITransport(app=app)
	async with AsyncClient(transport=transport, base_url="http://test") as async_client:
		yield async_client

	app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
	email = f"auth-{uuid.uuid4().hex}@example.com"
	password = "password123"

	await client.post(
		"/api/v1/auth/register",
		json={"email": email, "password": password},
	)
	login_res = await client.post(
		"/api/v1/auth/login",
		json={"email": email, "password": password},
	)
	token = login_res.json()["access_token"]
	return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def second_user_auth_headers(client: AsyncClient) -> dict[str, str]:
	email = f"second-{uuid.uuid4().hex}@example.com"
	password = "password123"

	await client.post(
		"/api/v1/auth/register",
		json={"email": email, "password": password},
	)
	login_res = await client.post(
		"/api/v1/auth/login",
		json={"email": email, "password": password},
	)
	token = login_res.json()["access_token"]
	return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def sample_txt_file() -> tuple[str, tuple[str, bytes, str]]:
	content = ("Hello world. " * 50).encode("utf-8")
	return ("files", ("test.txt", content, "text/plain"))


@pytest_asyncio.fixture
async def create_document_for_user(
	client: AsyncClient,
) -> Callable[[dict[str, str], bytes | None, str | None], Awaitable[dict]]:
	async def _create(
		auth_headers: dict[str, str],
		content: bytes | None = None,
		filename: str | None = None,
	) -> dict:
		file_content = content if content is not None else b"Hello world from helper"
		file_name = filename or f"doc-{uuid.uuid4().hex}.txt"
		payload = [("files", (file_name, file_content, "text/plain"))]
		response = await client.post(
			"/api/v1/documents/upload",
			files=payload,
			headers=auth_headers,
		)
		assert response.status_code == 201
		data = response.json()
		assert isinstance(data, list) and len(data) == 1
		return data[0]

	return _create
