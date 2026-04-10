from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers.auth import router as auth_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
	print("Database connected")
	yield


app = FastAPI(title="SEO Analyzer API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
	CORSMiddleware,
	allow_origins=[settings.FRONTEND_ORIGIN],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
	return {"status": "ok"}
