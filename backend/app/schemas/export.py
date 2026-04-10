from pydantic import BaseModel


class ExportRow(BaseModel):
    document_id: str
    filename: str
    word_count: int | None
    readability_score: float | None
    primary_keywords: str
    auto_summary: str | None
    user_edited_summary: str | None
    finalized_at: str | None
