# SEO Analyzer

Full-stack SEO content analyzer with async processing, live progress streaming, result review/finalize, export, and retry workflows.

## Tech Stack

- Backend: FastAPI, SQLAlchemy (async), Alembic
- Worker: Celery
- Broker + pub/sub + task results: Redis
- Database: PostgreSQL
- Frontend: Next.js 14 (App Router), TypeScript, MUI, Zustand, Axios
- Orchestration: Docker Compose

## What This App Does

- Register/login with JWT auth
- Upload one or multiple `.txt` files
- Create processing jobs and run async analysis in Celery
- Stream live job progress with SSE
- View metrics, keywords, and summaries on document detail page
- Edit summary drafts, finalize results, export JSON/CSV, and retry failed jobs

## Project Structure

```text
seo-analyzer/
├── README.md
├── docker-compose.yml
├── sample.txt
├── .env.example
├── backend/
│   ├── alembic.ini
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── requirements.txt
│   ├── .env.example
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       ├── 0001_initial_schema.py
│   │       ├── 0002_add_documents_and_jobs.py
│   │       └── 0003_add_extracted_results.py
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── dependencies/
│   │   │   ├── __init__.py
│   │   │   └── auth.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── document.py
│   │   │   ├── extracted_result.py
│   │   │   ├── processing_job.py
│   │   │   └── user.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── documents.py
│   │   │   ├── export.py
│   │   │   ├── jobs.py
│   │   │   └── results.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── document.py
│   │   │   ├── export.py
│   │   │   ├── job.py
│   │   │   └── result.py
│   │   ├── scripts/
│   │   │   ├── __init__.py
│   │   │   └── seed.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── document_service.py
│   │   │   ├── event_publisher.py
│   │   │   ├── export_service.py
│   │   │   ├── job_service.py
│   │   │   └── result_service.py
│   │   └── workers/
│   │       ├── __init__.py
│   │       ├── celery_app.py
│   │       └── tasks.py
│   ├── services/
│   │   └── analysis_engine.py
│   └── tests/
│       ├── conftest.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── test_auth.py
│       │   ├── test_documents.py
│       │   ├── test_export.py
│       │   ├── test_finalize.py
│       │   ├── test_result.py
│       │   ├── test_retry.py
│       │   └── test_upload.py
│       ├── integration/
│       │   ├── __init__.py
│       │   ├── test_retry_idempotency.py
│       │   └── test_worker_pipeline.py
│       └── unit/
│           ├── __init__.py
│           └── test_analysis_engine.py
├── frontend/
│   ├── README.md
│   ├── next.config.mjs
│   ├── package.json
│   ├── postcss.config.mjs
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── .eslintrc.json
│   └── src/
│       ├── app/
│       │   ├── globals.css
│       │   ├── layout.tsx
│       │   ├── page.tsx
│       │   ├── (auth)/
│       │   │   ├── login/
│       │   │   │   └── page.tsx
│       │   │   └── register/
│       │   │       └── page.tsx
│       │   ├── dashboard/
│       │   │   └── page.tsx
│       │   ├── documents/
│       │   │   └── [id]/
│       │   │       └── page.tsx
│       │   └── fonts/
│       │       ├── GeistMonoVF.woff
│       │       └── GeistVF.woff
│       ├── components/
│       │   ├── features/
│       │   │   ├── dashboard/
│       │   │   │   ├── DocumentTable.tsx
│       │   │   │   ├── FilterBar.tsx
│       │   │   │   ├── JobProgressBar.tsx
│       │   │   │   └── StatusBadge.tsx
│       │   │   ├── detail/
│       │   │   │   ├── FinalizeButton.tsx
│       │   │   │   ├── KeywordsTable.tsx
│       │   │   │   ├── MetricsPanel.tsx
│       │   │   │   └── SummaryEditor.tsx
│       │   │   ├── export/
│       │   │   │   └── ExportButtons.tsx
│       │   │   └── upload/
│       │   │       └── UploadZone.tsx
│       │   └── providers/
│       │       └── AppProviders.tsx
│       ├── context/
│       │   └── AuthContext.tsx
│       ├── hooks/
│       │   ├── useDocumentDetail.ts
│       │   ├── useDocuments.ts
│       │   └── useSSE.ts
│       ├── lib/
│       │   └── api.ts
│       ├── store/
│       │   ├── documentStore.ts
│       │   └── progressStore.ts
│       └── types/
│           ├── auth.ts
│           └── document.ts
└── storage/
    └── uploads/
        └── .gitkeep
```

## Prerequisites

- Docker Desktop (or Docker Engine + Compose)
- Node.js 18+ (for local frontend development outside Docker)

## Setup Instructions

1. Copy environment file:

```bash
cp .env.example .env
```

2. Ensure `.env` includes values similar to:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/seo_analyzer
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=seo_analyzer
REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=change_this_to_a_long_random_string_at_least_32_chars
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24
UPLOAD_DIR=./storage/uploads
MAX_UPLOAD_SIZE_BYTES=5242880
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
FRONTEND_ORIGIN=http://localhost:3000
```

## Run Steps

1. Build and start services:

```bash
docker compose up --build -d
```

2. Run migrations:

```bash
docker compose exec api alembic upgrade head
```

3. Verify health:

```bash
curl http://localhost:8000/health
docker compose exec redis redis-cli ping
docker compose exec worker celery -A app.workers.celery_app inspect ping
```

4. Start frontend (local dev):

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## Architecture Overview

This system uses an async pipeline so uploads return quickly while analysis runs in the background.

- Frontend (Next.js): auth, upload UI, dashboard, detail view, SSE subscription
- API (FastAPI): authentication, document/job/result APIs, export endpoints
- Worker (Celery): background text analysis and retry handling
- PostgreSQL: source of truth for users, documents, jobs, and extracted results
- Redis: Celery broker/result backend and SSE progress pub/sub transport
- Shared storage: uploaded `.txt` files consumed by API and worker containers

High-level flow:

1. User uploads file(s) from frontend.
2. API validates, stores files, creates document/job rows, commits.
3. API dispatches Celery task(s) to Redis broker.
4. Worker processes files and publishes progress updates.
5. SSE endpoint streams job progress to frontend.
6. User reviews, edits, finalizes, and exports results.

## System Design

The project is designed as a decoupled web + worker architecture with clear responsibilities.

- Command side (API + worker): handles uploads, job creation, analysis execution, retries, and result persistence
- Query side (API + frontend): serves document lists/details, progress state, and exports for finalized results
- Data consistency model: PostgreSQL is the system of record; Redis is used for transient queueing/progress signals
- Failure handling: job status machine (`queued -> processing -> completed/failed -> finalized`) and retry endpoint guardrails prevent invalid transitions
- Idempotency strategy: extracted result writes use upsert semantics so retries do not duplicate rows

This structure keeps user-facing latency low while preserving reliability under transient worker failures.

## Async Workflow Execution

Async execution is implemented as a transactional handoff between API and worker.

1. API validates files and creates `documents` + `processing_jobs` records.
2. API commits DB transaction before dispatching Celery tasks.
3. Worker consumes tasks from Redis and updates progress stage/percentage.
4. Progress is persisted and published via Redis pub/sub.
5. SSE endpoint forwards updates to frontend subscribers in near real time.
6. Worker upserts extracted results and marks job terminal state.

Key reliability behaviors:

- Retry-safe result persistence (upsert by document)
- Preserves user-edited summary on re-analysis
- Explicit failed-state retry endpoint restricted to failed jobs
- Graceful handling for missing files and max-retry exhaustion

## Implementation Quality

Implementation quality is enforced through layered architecture and automated tests.

- Separation of concerns: routers (transport), services (business logic), workers (async execution), schemas (contracts)
- Type safety: TypeScript frontend + Pydantic/FastAPI backend response modeling
- Test coverage: unit, API, and integration tests, including retry/idempotency behavior
- Operational clarity: health checks, seed script, and reproducible Docker setup
- Developer ergonomics: explicit env templates, scriptable migration flow, and documented troubleshooting

Current quality baseline:

- Frontend production build passes (`npm run build`)
- Backend test suite passes (`pytest tests/ -v --tb=short`)

## Seed Data (Test Login + 3 Documents)

This repository includes an idempotent seed script:

- Script path: `backend/app/scripts/seed.py`

Run seed:

```bash
docker compose exec api python -m app.scripts.seed
```

Seeded credentials:

- Email: `seed.user@example.com`
- Password: `SeedPass123!`

Seeded documents for that user:

- `seed_finalized.txt` (job status: `finalized`, includes extracted result)
- `seed_processing.txt` (job status: `processing`)
- `seed_failed.txt` (job status: `failed` for retry testing)

The seed script resets existing documents for this seed user each run so you can re-run safely.

## API Overview

Base URL: `http://localhost:8000/api/v1`

Auth:

- `POST /auth/register`
- `POST /auth/login`

Documents:

- `POST /documents/upload`
- `GET /documents`
- `GET /documents/{document_id}`

Jobs:

- `GET /jobs/{job_id}/progress/stream` (SSE)
- `POST /jobs/{job_id}/retry`

Results:

- `PATCH /documents/{document_id}/result`
- `POST /documents/{document_id}/finalize`

Export:

- `GET /documents/{document_id}/export?format=json|csv`
- `GET /export/bulk?format=csv`

## How Processing Works

1. Upload endpoint stores files in `storage/uploads`
2. Backend creates `documents` + `processing_jobs` rows
3. Backend commits, then dispatches Celery tasks
4. Celery worker reads queued tasks from Redis broker
5. Worker updates DB progress and publishes progress events to Redis pub/sub
6. SSE endpoint streams progress events to frontend
7. Dashboard/detail UI reflects job state and progress

## Testing

Run all backend tests:

```bash
docker compose exec api pytest tests/ -v --tb=short
```

Run key module tests:

```bash
docker compose exec api pytest tests/api/test_upload.py -v
docker compose exec api pytest tests/api/test_documents.py -v
docker compose exec api pytest tests/api/test_result.py tests/api/test_finalize.py -v
docker compose exec api pytest tests/api/test_export.py -v
docker compose exec api pytest tests/api/test_retry.py tests/integration/test_retry_idempotency.py -v
```

## Common Commands

```bash
# Rebuild only API after backend code changes
docker compose build api
docker compose up -d api

# Rebuild worker when Celery/task code changes
docker compose build worker
docker compose up -d worker

# Check running services
docker compose ps

# Tail logs
docker compose logs -f api
docker compose logs -f worker
docker compose logs -f redis
```

## Assumptions

- Input files are UTF-8 plain text (`text/plain`, `.txt`).
- Redis and PostgreSQL are reachable from API and worker at startup.
- Upload directory is shared between API and worker (`storage/uploads`).
- JWT auth is sufficient for this project scope (no OAuth/SSO requirement).
- Single-region deployment is acceptable for latency and consistency.

## Tradeoffs

- Celery + Redis chosen over simpler in-process jobs for reliability and retries, at cost of extra operational complexity.
- SSE chosen for one-way real-time progress (simpler than WebSockets), but only supports server-to-client updates.
- Local/shared file storage simplifies development, but is less portable than object storage for large-scale cloud setups.
- Readability/keyword heuristics favor speed and determinism over NLP model sophistication.
- Docker Compose provides fast local orchestration, but is not a full production orchestrator.

## Limitations

- Only `.txt` uploads are supported currently (no PDF/DOCX parsing).
- Very large files are blocked by configured upload size limits.
- No tenant-level rate limiting or advanced abuse protection yet.
- Background worker scaling is manual in Compose-based deployments.
- Export and analytics are tied to finalized results only.
- Current auth/session approach uses JWT in browser storage and requires careful production hardening.

## Troubleshooting

### Uploads stay queued too long

- Confirm worker is running:

```bash
docker compose ps
docker compose logs worker --tail=100
```

- Confirm Celery can talk through Redis:

```bash
docker compose exec worker celery -A app.workers.celery_app inspect ping
```

- Confirm Redis is healthy:

```bash
docker compose exec redis redis-cli ping
docker compose exec redis redis-cli info keyspace
```

- If code changes are not reflected in containers, rebuild the affected service.

### Frontend status not updating

- Verify frontend points to backend: `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`
- Verify browser has JWT in localStorage key `seo_jwt`
- Verify `/jobs/{job_id}/progress/stream?token=...` is reachable

### Database issues

- Ensure migrations are applied:

```bash
docker compose exec api alembic upgrade head
```

## Security Notes

- Development credentials in seed data are for local use only
- Replace `JWT_SECRET_KEY` with a strong secret in real environments
- Restrict CORS origins in production

## License

Internal/demo use unless a dedicated project license is added.
