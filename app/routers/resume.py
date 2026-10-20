from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import require_admin_session
from .. import models, schemas, storage

router = APIRouter(prefix="/resume", tags=["resume"])

ALLOWED_CONTENT_TYPES = {"application/pdf"}
MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


@router.get("", response_model=schemas.ResumeOut)
def get_resume(db: Session = Depends(get_db)):
    resume = db.scalar(select(models.Resume).order_by(models.Resume.id.desc()))
    if not resume:
        raise HTTPException(status_code=404, detail="No resume uploaded yet")
    return resume


@router.post("", response_model=schemas.ResumeOut, dependencies=[Depends(require_admin_session)])
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    file_bytes = await file.read()
    if len(file_bytes) > MAX_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File too large (10 MB max)")

    existing = db.scalar(select(models.Resume).order_by(models.Resume.id.desc()))
    key, url = storage.upload_file(file_bytes, file.filename or "resume.pdf", file.content_type)

    if existing:
        storage.delete_file(existing.object_key)
        existing.object_key = key
        existing.url = url
        existing.original_filename = file.filename or "resume.pdf"
        resume = existing
    else:
        resume = models.Resume(object_key=key, url=url, original_filename=file.filename or "resume.pdf")
        db.add(resume)

    db.commit()
    db.refresh(resume)
    return resume
