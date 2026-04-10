from app.workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60, name="tasks.analyze_document")
def analyze_document(self, job_id: str, document_id: str, file_path: str):
    # STUB for now — just prints. Full implementation in Module 4.
    print(f"[STUB] analyze_document called: job={job_id}, doc={document_id}, path={file_path}")
    return {"status": "stub"}
