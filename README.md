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
	backend/
		app/
			dependencies/
			models/
			routers/
			schemas/
			scripts/
			services/
			workers/
			main.py
		alembic/
		tests/
	frontend/
		src/
			app/
			components/
			context/
			hooks/
			lib/
			store/
			types/
	storage/uploads/
	docker-compose.yml
```

## Prerequisites

- Docker Desktop (or Docker Engine + Compose)
- Node.js 18+ (for local frontend development outside Docker)

## Environment Setup

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

## Quick Start

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
