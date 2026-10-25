from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..security import require_admin_session

router = APIRouter(
    prefix="/admin/dashboard",
    tags=["admin dashboard"],
    dependencies=[Depends(require_admin_session)],
)


@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Return live portfolio content counts for the authenticated admin dashboard."""
    return {
        "projects": db.scalar(select(func.count()).select_from(models.Project)) or 0,
        "skills": db.scalar(select(func.count()).select_from(models.Skill)) or 0,
        "qualifications": db.scalar(
            select(func.count()).select_from(models.Qualification)
        )
        or 0,
        "content_blocks": db.scalar(
            select(func.count()).select_from(models.ContentBlock)
        )
        or 0,
        "resume_configured": (
            db.scalar(select(func.count()).select_from(models.Resume)) or 0
        )
        > 0,
        "database": "connected",
    }
