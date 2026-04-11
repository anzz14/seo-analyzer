from collections.abc import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


async_engine = create_async_engine(
	settings.DATABASE_URL,
	pool_size=5,
	max_overflow=10,
)

SYNC_DATABASE_URL = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
sync_engine = create_engine(SYNC_DATABASE_URL)
SyncSession = sessionmaker(sync_engine)


class Base(DeclarativeBase):
	pass


AsyncSessionLocal = async_sessionmaker(
	bind=async_engine,
	class_=AsyncSession,
	expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
	async with AsyncSessionLocal() as session:
		try:
			yield session
			await session.commit()
		except Exception:
			await session.rollback()
			raise
		finally:
			await session.close()
