"""add extracted results table

Revision ID: 0003_add_extracted_results
Revises: 0002_add_documents_and_jobs
Create Date: 2026-04-10 00:00:02
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0003_add_extracted_results"
down_revision: str | None = "0002_add_documents_and_jobs"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "extracted_results",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("readability_score", sa.Float(), nullable=True),
        sa.Column("primary_keywords", sa.JSON(), nullable=True),
        sa.Column("auto_summary", sa.Text(), nullable=True),
        sa.Column("user_edited_summary", sa.Text(), nullable=True),
        sa.Column("is_finalized", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["processing_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", name="uq_extracted_results_document_id"),
    )


def downgrade() -> None:
    op.drop_table("extracted_results")
