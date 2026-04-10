import json

from celery.exceptions import MaxRetriesExceededError
from sqlalchemy import text

from app.database import SyncSession
from app.services.event_publisher import publish_and_persist
from app.workers.celery_app import celery_app
from services.analysis_engine import compute_all


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60, name="tasks.analyze_document")
def analyze_document(self, job_id: str, document_id: str, file_path: str):
    with SyncSession() as db:
        try:
            db.execute(
                text(
                    """
                    UPDATE processing_jobs
                    SET status = 'processing',
                        started_at = NOW(),
                        error_message = NULL
                    WHERE id = :job_id
                    """
                ),
                {"job_id": job_id},
            )
            db.commit()

            publish_and_persist(db, job_id, "reading_file", 10, "Reading file...")

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text_content = f.read()
            except FileNotFoundError:
                db.execute(
                    text(
                        """
                        UPDATE processing_jobs
                        SET status = 'failed',
                            error_message = 'File not found'
                        WHERE id = :job_id
                        """
                    ),
                    {"job_id": job_id},
                )
                db.commit()
                publish_and_persist(db, job_id, "job_failed", 0, "File not found")
                return

            publish_and_persist(db, job_id, "analyzing", 30, "Computing metrics...")
            results = compute_all(text_content)

            publish_and_persist(db, job_id, "saving_results", 70, "Saving results...")

            db.execute(
                text(
                    """
                    INSERT INTO extracted_results (
                        document_id,
                        job_id,
                        word_count,
                        readability_score,
                        primary_keywords,
                        auto_summary,
                        user_edited_summary
                    )
                    VALUES (
                        :document_id,
                        :job_id,
                        :word_count,
                        :readability_score,
                        CAST(:primary_keywords AS JSON),
                        :auto_summary,
                        NULL
                    )
                    ON CONFLICT (document_id)
                    DO UPDATE SET
                        word_count = EXCLUDED.word_count,
                        readability_score = EXCLUDED.readability_score,
                        primary_keywords = EXCLUDED.primary_keywords,
                        auto_summary = EXCLUDED.auto_summary,
                        job_id = EXCLUDED.job_id,
                        user_edited_summary = COALESCE(extracted_results.user_edited_summary, EXCLUDED.user_edited_summary),
                        updated_at = NOW()
                    """
                ),
                {
                    "document_id": document_id,
                    "job_id": job_id,
                    "word_count": results.get("word_count"),
                    "readability_score": results.get("readability_score"),
                    "primary_keywords": json.dumps(results.get("primary_keywords", [])),
                    "auto_summary": results.get("auto_summary"),
                },
            )
            db.commit()

            db.execute(
                text(
                    """
                    UPDATE processing_jobs
                    SET status = 'completed',
                        progress_percentage = 100,
                        completed_at = NOW(),
                        error_message = NULL
                    WHERE id = :job_id
                    """
                ),
                {"job_id": job_id},
            )
            db.commit()
            publish_and_persist(db, job_id, "job_completed", 100, "Analysis complete")
        except Exception as exc:
            db.rollback()
            try:
                raise self.retry(exc=exc)
            except MaxRetriesExceededError:
                error_text = str(exc)
                db.execute(
                    text(
                        """
                        UPDATE processing_jobs
                        SET status = 'failed',
                            error_message = :error_message
                        WHERE id = :job_id
                        """
                    ),
                    {
                        "job_id": job_id,
                        "error_message": error_text,
                    },
                )
                db.commit()
                publish_and_persist(db, job_id, "job_failed", 0, error_text)
