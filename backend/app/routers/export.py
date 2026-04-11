from __future__ import annotations

import csv
import json
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services import export_service

router = APIRouter(tags=["export"], dependencies=[Depends(get_current_user)])


@router.get("/documents/{document_id}/export")
async def export_document(
    document_id: str,
    format: str = Query("json"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    normalized_format = format.lower()

    payload = await export_service.build_json_export(db, document_id, current_user.id)

    if normalized_format == "json":
        return JSONResponse(content=payload)

    if normalized_format == "csv":
        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "document_id",
                "filename",
                "word_count",
                "readability_score",
                "primary_keywords",
                "auto_content",
                "user_edited_content",
                "finalized_at",
            ]
        )
        writer.writerow(
            [
                payload.get("document_id"),
                payload.get("filename"),
                payload.get("word_count"),
                payload.get("readability_score"),
                json.dumps(payload.get("primary_keywords") or []),
                payload.get("auto_summary"),
                payload.get("user_edited_summary"),
                payload.get("finalized_at"),
            ]
        )
        # Add UTF-8 BOM so spreadsheet apps detect encoding correctly.
        csv_content = "\ufeff" + buffer.getvalue()
        return Response(
            content=csv_content,
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename={document_id}.csv",
            },
        )

    raise HTTPException(status_code=400, detail="format must be 'json' or 'csv'")


@router.get("/export/bulk")
async def export_bulk(
    format: str = Query("csv"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    normalized_format = format.lower()
    if normalized_format != "csv":
        raise HTTPException(status_code=400, detail="bulk export only supports csv")

    async def stream_with_bom():
        yield "\ufeff"
        async for chunk in export_service.stream_csv_rows(db, current_user.id):
            yield chunk

    return StreamingResponse(
        stream_with_bom(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=bulk_export.csv"},
    )
