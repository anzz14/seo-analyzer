from __future__ import annotations

import csv
import json
from io import StringIO
from typing import AsyncGenerator
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.extracted_result import ExtractedResult


async def build_json_export(
    db: AsyncSession,
    document_id: str | UUID,
    user_id: str | UUID,
) -> dict:
    document_result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == user_id)
    )
    document = document_result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    result_query = await db.execute(
        select(ExtractedResult).where(ExtractedResult.document_id == document.id)
    )
    extracted = result_query.scalar_one_or_none()
    if extracted is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result not found")

    if not extracted.is_finalized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Export requires finalized result",
        )

    return {
        "document_id": str(document.id),
        "filename": document.original_filename,
        "word_count": extracted.word_count,
        "readability_score": extracted.readability_score,
        "primary_keywords": extracted.primary_keywords or [],
        "auto_summary": extracted.auto_summary,
        "user_edited_summary": extracted.user_edited_summary,
        "finalized_at": extracted.finalized_at.isoformat() if extracted.finalized_at else None,
    }


def _csv_row_to_string(row: list[str | int | float | None]) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(row)
    return buffer.getvalue()


async def stream_csv_rows(
    db: AsyncSession,
    user_id: str | UUID,
) -> AsyncGenerator[str, None]:
    header = [
        "document_id",
        "filename",
        "word_count",
        "readability_score",
        "primary_keywords",
        "auto_content",
        "user_edited_content",
        "finalized_at",
    ]
    yield _csv_row_to_string(header)

    query = (
        select(ExtractedResult, Document)
        .join(Document, Document.id == ExtractedResult.document_id)
        .where(Document.user_id == user_id, ExtractedResult.is_finalized.is_(True))
        .order_by(ExtractedResult.finalized_at.desc().nullslast(), ExtractedResult.created_at.desc())
        .execution_options(yield_per=100)
    )

    stream = await db.stream(query)
    async for extracted, document in stream:
        yield _csv_row_to_string(
            [
                str(document.id),
                document.original_filename,
                extracted.word_count,
                extracted.readability_score,
                json.dumps(extracted.primary_keywords or []),
                extracted.auto_summary,
                extracted.user_edited_summary,
                extracted.finalized_at.isoformat() if extracted.finalized_at else None,
            ]
        )
