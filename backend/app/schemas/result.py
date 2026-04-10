from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ExtractedResultResponse(BaseModel):
    id: str
    document_id: str
    job_id: str
    word_count: int | None
    readability_score: float | None
    primary_keywords: list[dict] | None
    auto_summary: str | None
    user_edited_summary: str | None
    is_finalized: bool
    finalized_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PatchResultRequest(BaseModel):
    user_edited_summary: str = Field(min_length=1, max_length=5000)
