from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.job import JobResponse
from app.schemas.result import ExtractedResultResponse


class DocumentResponse(BaseModel):
    id: str
    user_id: str
    original_filename: str
    file_size: int
    mime_type: str
    upload_timestamp: datetime
    created_at: datetime
    latest_job: JobResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int


class DocumentDetailResponse(DocumentResponse):
    latest_job: JobResponse | None = None
    result: ExtractedResultResponse | None = None
