import os
from datetime import datetime
from sqlalchemy.orm import Session

from .worker import celery_app
from .db import SessionLocal
from . import models
from .config import settings
from .services.extract import extract_transactions
from .services.export import export_csv, export_json
from .utils.files import ensure_dir

@celery_app.task(name="convert_pdf")
def convert_pdf(conversion_id: int) -> None:
    db: Session = SessionLocal()
    try:
        conv = db.query(models.Conversion).filter(models.Conversion.id == conversion_id).first()
        if not conv:
            return

        conv.status = "processing"
        db.commit()

        ensure_dir(settings.STORAGE_DIR)
        res = extract_transactions(conv.storage_pdf_path)

        # export
        out_csv = os.path.join(settings.STORAGE_DIR, f"conversion_{conv.id}.csv")
        out_json = os.path.join(settings.STORAGE_DIR, f"conversion_{conv.id}.json")
        export_csv(res.rows, out_csv)
        export_json(res.rows, res.meta, out_json)

        conv.output_csv_path = out_csv
        conv.output_json_path = out_json
        conv.pages = res.meta.get("pages") or 0
        conv.status = "done" if res.rows else "failed"
        if not res.rows:
            conv.error_message = "No transactions detected. Try a different statement or enable OCR improvements."
        conv.completed_at = datetime.utcnow()
        db.commit()
    except Exception as e:
        try:
            conv = db.query(models.Conversion).filter(models.Conversion.id == conversion_id).first()
            if conv:
                conv.status = "failed"
                conv.error_message = str(e)
                conv.completed_at = datetime.utcnow()
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
