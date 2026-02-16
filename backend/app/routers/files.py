from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..config import settings
from .. import models
from ..utils.files import save_upload_pdf
from ..tasks import convert_pdf

router = APIRouter(prefix="/files", tags=["files"])

@router.post("/upload")
def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Basic page limits by role (very light MVP logic)
    role = user.role or "free"
    max_mb = 10 if role == "free" else 30
    content = file.file.read()
    if len(content) > max_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File too large. Limit is {max_mb}MB for your plan.")
    file.file.seek(0)

    original_name, stored_path = save_upload_pdf(file, settings.STORAGE_DIR)
    conv = models.Conversion(
        user_id=user.id,
        filename=original_name,
        storage_pdf_path=stored_path,
        status="queued",
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)

    convert_pdf.delay(conv.id)
    return {"conversion_id": conv.id, "status": conv.status}
