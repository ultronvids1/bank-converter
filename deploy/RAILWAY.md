# Deploy on Railway (MVP)

## Services you need
- Postgres
- Redis
- API (FastAPI)
- Worker (Celery)
- Frontend (Vite)

## Steps (copy-paste friendly)

### 1) Create a new Railway project
- New Project → Deploy from GitHub Repo

### 2) Add Postgres + Redis
- Add → Database → Postgres
- Add → Database → Redis

### 3) Set variables (Project → Variables)
Set:
- `APP_ENV=prod`
- `SECRET_KEY=<long random>`
- `BACKEND_CORS_ORIGINS=<your frontend url>`
- `DATABASE_URL=<Railway postgres url>`  (Railway gives this)
- `REDIS_URL=<Railway redis url>`        (Railway gives this)
- `STORAGE_DIR=/app/storage`

Optional Stripe:
- `STRIPE_SECRET_KEY=...`
- `STRIPE_WEBHOOK_SECRET=...`
- `STRIPE_PRICE_ID=...`

### 4) Create API service
- Service settings:
  - Root directory: `backend`
  - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  - Healthcheck: `/health`

### 5) Create Worker service
- Root directory: `backend`
- Start command: `celery -A app.worker.celery_app worker -l info`

### 6) Create Frontend service
- Root directory: `frontend`
- Build command: `npm ci && npm run build`
- Start command: `npm run preview -- --host 0.0.0.0 --port $PORT`
- Set `VITE_API_BASE=<your API service URL>`

### 7) Update CORS
Set `BACKEND_CORS_ORIGINS` to your frontend domain (comma-separated if multiple).

Done.
