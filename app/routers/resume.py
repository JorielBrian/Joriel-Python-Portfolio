from io import BytesIO
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas, storage
from ..database import get_db
from ..security import require_admin_session

router = APIRouter(prefix="/resume", tags=["resume"])

ALLOWED_CONTENT_TYPES = {"application/pdf"}
MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
DOWNLOAD_PATH = "/resume/download"


def _safe_filename(filename: str | None) -> str:
    # Remove client-supplied path components and control characters.
    name = Path((filename or "resume.pdf").replace("\\", "/")).name
    name = "".join(char for char in name if char.isprintable() and char not in "\r\n")
    return name[:180] or "resume.pdf"


@router.get("", response_model=schemas.ResumeOut)
def get_resume(db: Session = Depends(get_db)):
    resume = db.scalar(select(models.Resume).order_by(models.Resume.id.desc()))
    if not resume:
        raise HTTPException(status_code=404, detail="No resume uploaded yet")

    # Never expose the private bucket's object URL to the browser.
    resume.url = DOWNLOAD_PATH
    return resume


@router.get("/view")
def view_resume(db: Session = Depends(get_db)):
    resume = db.scalar(select(models.Resume).order_by(models.Resume.id.desc()))
    if not resume:
        raise HTTPException(status_code=404, detail="No resume uploaded yet")

    try:
        file_bytes = storage.download_file(resume.object_key)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Unable to retrieve the CV from storage") from exc

    filename = _safe_filename(resume.original_filename)
    content_disposition = (
        'inline; filename="resume.pdf"; '
        f"filename*=UTF-8''{quote(filename)}"
    )
    return StreamingResponse(
        BytesIO(file_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": content_disposition},
    )


@router.get("/download")
def download_resume(db: Session = Depends(get_db)):
    resume = db.scalar(select(models.Resume).order_by(models.Resume.id.desc()))
    if not resume:
        raise HTTPException(status_code=404, detail="No resume uploaded yet")

    try:
        file_bytes = storage.download_file(resume.object_key)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Unable to retrieve the CV from storage") from exc

    filename = _safe_filename(resume.original_filename)
    content_disposition = (
        'attachment; filename="resume.pdf"; '
        f"filename*=UTF-8''{quote(filename)}"
    )
    return StreamingResponse(
        BytesIO(file_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": content_disposition},
    )


@router.post(
    "",
    response_model=schemas.ResumeOut,
    dependencies=[Depends(require_admin_session)],
)
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="The selected file is empty")
    if len(file_bytes) > MAX_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File too large (10 MB max)")
    if not file_bytes.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="The selected file is not a valid PDF")

    filename = _safe_filename(file.filename)
    existing = db.scalar(select(models.Resume).order_by(models.Resume.id.desc()))
    old_key = existing.object_key if existing else None

    # Upload first, then commit the new metadata. The old object is deleted only
    # after the database commit succeeds, so a failed replacement keeps the old CV.
    key = storage.upload_file(file_bytes, filename, "application/pdf")
    resume = existing
    if resume:
        resume.object_key = key
        resume.url = DOWNLOAD_PATH
        resume.original_filename = filename
    else:
        resume = models.Resume(
            object_key=key,
            url=DOWNLOAD_PATH,
            original_filename=filename,
        )
        db.add(resume)

    try:
        db.commit()
        db.refresh(resume)
    except Exception:
        db.rollback()
        storage.delete_file(key)
        raise

    if old_key and old_key != key:
        storage.delete_file(old_key)

    resume.url = DOWNLOAD_PATH
    return resume
