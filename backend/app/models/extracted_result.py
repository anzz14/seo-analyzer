from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ExtractedResult(Base):
    __tablename__ = "extracted_results"
    __table_args__ = (UniqueConstraint("document_id", name="uq_extracted_results_document_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("processing_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    readability_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    primary_keywords: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    auto_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_edited_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_finalized: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    document: Mapped["Document"] = relationship("Document", back_populates="extracted_result")
    job: Mapped["ProcessingJob"] = relationship("ProcessingJob")
