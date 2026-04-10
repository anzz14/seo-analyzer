from datetime import datetime

from pydantic import BaseModel, ConfigDict


class JobResponse(BaseModel):
    id: str
    document_id: str
    status: str
    progress_percentage: int
    current_stage: str
    error_message: str | None
    retry_count: int
    celery_task_id: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UploadResponse(BaseModel):
    document_id: str
    job_id: str
    filename: str
    file_size: int
