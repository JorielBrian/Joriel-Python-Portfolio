from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import require_admin_session
from .. import models, schemas

router = APIRouter(prefix="/content", tags=["content"])


@router.get("", response_model=list[schemas.ContentBlockOut])
def list_content(db: Session = Depends(get_db)):
    return db.scalars(select(models.ContentBlock)).all()


@router.get("/{key}", response_model=schemas.ContentBlockOut)
def get_content(key: str, db: Session = Depends(get_db)):
    block = db.scalar(select(models.ContentBlock).where(models.ContentBlock.key == key.upper()))
    if not block:
        raise HTTPException(status_code=404, detail="Content block not found")
    return block


@router.put("/{key}", response_model=schemas.ContentBlockOut, dependencies=[Depends(require_admin_session)])
def update_content(key: str, payload: schemas.ContentBlockUpdate, db: Session = Depends(get_db)):
    key = key.upper()
    block = db.scalar(select(models.ContentBlock).where(models.ContentBlock.key == key))
    if not block:
        block = models.ContentBlock(key=key, paragraphs=payload.paragraphs)
        db.add(block)
    else:
        block.paragraphs = payload.paragraphs
    db.commit()
    db.refresh(block)
    return block
