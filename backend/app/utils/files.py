import os, uuid
from fastapi import UploadFile, HTTPException
from pathlib import Path

ALLOWED_MIME = {"application/pdf"}
ALLOWED_EXT = {".pdf"}

def ensure_dir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)

def save_upload_pdf(upload: UploadFile, storage_dir: str) -> tuple[str, str]:
    filename = upload.filename or "statement.pdf"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="Only PDF uploads are allowed")

    if upload.content_type not in ALLOWED_MIME:
        raise HTTPException(status_code=400, detail="Invalid content type (PDF required)")

    ensure_dir(storage_dir)
    uid = str(uuid.uuid4())
    dest = os.path.join(storage_dir, f"{uid}.pdf")

    with open(dest, "wb") as f:
        f.write(upload.file.read())

    return filename, dest
