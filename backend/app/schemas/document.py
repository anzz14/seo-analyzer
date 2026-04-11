from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.job import JobResponse


class ExtractedResultResponse(BaseModel):
    id: str
    document_id: str
    word_count: int | None = None
    readability_score: float | None = None
    primary_keywords: list[dict] | None = None
    auto_summary: str | None = None
    user_edited_summary: str | None = None
    is_finalized: bool = False
    finalized_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(BaseModel):
    id: str
    user_id: str
    original_filename: str
    file_size: int
    mime_type: str
    upload_timestamp: datetime
    created_at: datetime
    latest_job: JobResponse | None = None
    result: ExtractedResultResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int
