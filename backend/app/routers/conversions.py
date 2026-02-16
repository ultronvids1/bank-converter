import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from .. import models
from ..schemas import ConversionOut

router = APIRouter(prefix="/conversions", tags=["conversions"])

@router.get("/", response_model=list[ConversionOut])
def list_conversions(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(models.Conversion).filter(models.Conversion.user_id == user.id).order_by(models.Conversion.id.desc()).all()

@router.get("/{conversion_id}", response_model=ConversionOut)
def get_conversion(conversion_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    conv = db.query(models.Conversion).filter(models.Conversion.id == conversion_id, models.Conversion.user_id == user.id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Not found")
    return conv

@router.get("/{conversion_id}/download/csv")
def download_csv(conversion_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    conv = db.query(models.Conversion).filter(models.Conversion.id == conversion_id, models.Conversion.user_id == user.id).first()
    if not conv or conv.status != "done" or not conv.output_csv_path:
        raise HTTPException(status_code=404, detail="File not available")
    return FileResponse(conv.output_csv_path, filename=f"{conv.filename}.csv")

@router.get("/{conversion_id}/download/json")
def download_json(conversion_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    conv = db.query(models.Conversion).filter(models.Conversion.id == conversion_id, models.Conversion.user_id == user.id).first()
    if not conv or conv.status not in {"done","failed"} or not conv.output_json_path:
        raise HTTPException(status_code=404, detail="File not available")
    return FileResponse(conv.output_json_path, filename=f"{conv.filename}.json")
