FROM python:3.11-slim

# System deps for PDF + OCR
RUN apt-get update && apt-get install -y --no-install-recommends     build-essential     poppler-utils     tesseract-ocr     libgl1     libglib2.0-0     ghostscript     && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app/app

ENV PYTHONUNBUFFERED=1

# default command for API service (overridden for worker in docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
