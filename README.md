# Bank Statement Converter (MVP)

This is a production-minded MVP for a bank-statement converter web app (PDF -> CSV/Excel/JSON).

## What's included
- **Backend API**: FastAPI + SQLAlchemy + JWT auth
- **Async processing**: Celery workers + Redis
- **Storage**: Local by default (S3-ready hook points)
- **Extraction pipeline**: pdfplumber -> Camelot (lattice/stream) -> PyMuPDF -> OCR (pdf2image + Tesseract)
- **Outputs**: CSV (MVP), JSON (MVP); Excel scaffold included
- **Frontend**: React (Vite) + Tailwind (upload, status, history)
- **Docker**: docker-compose for local dev

## Quick start (Docker)
1. Install Docker Desktop
2. From repo root:

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend:  http://localhost:8000/docs

## Quick start (local)
Backend:
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Worker:
```bash
cd backend
source .venv/bin/activate
celery -A app.worker.celery_app worker -l info
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

## Notes
- This MVP stores uploaded PDFs/results on disk under `backend/storage/` and deletes nothing automatically.
  In production, you should:
  - upload to S3 (or similar)
  - enforce short retention (e.g., 30–120 minutes)
  - add virus scanning (ClamAV)
- OCR requires Tesseract and Poppler (included in the Docker image).

## Deploy (simple)
- Recommended for MVP: **Railway** or **Render**
- You’ll need:
  - Postgres
  - Redis
  - Two services: `api` and `worker`
  - One static site / web service for frontend

See `deploy/RAILWAY.md` for copy-paste deployment steps.
