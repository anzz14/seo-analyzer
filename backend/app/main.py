from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers.auth import router as auth_router
from app.routers import documents as documents_router
from app.routers import export as export_router
from app.routers import jobs as jobs_router
from app.routers import results as results_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
	os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
	print("Database connected")
	yield


app = FastAPI(title="SEO Analyzer API", version="1.0.0", lifespan=lifespan)

allowed_origins = sorted(
	{
		settings.FRONTEND_ORIGIN,
		"http://localhost:3000",
		"http://localhost:3001",
		"http://127.0.0.1:3000",
		"http://127.0.0.1:3001",
	}
)

app.add_middleware(
	CORSMiddleware,
	allow_origins=allowed_origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(documents_router.router, prefix="/api/v1")
app.include_router(export_router.router, prefix="/api/v1")
app.include_router(jobs_router.router, prefix="/api/v1")
app.include_router(results_router.router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
	return {"status": "ok"}
