from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import require_admin_session
from .. import models, schemas

router = APIRouter(prefix="/qualifications", tags=["qualifications"])


@router.get("", response_model=list[schemas.QualificationOut])
def list_qualifications(db: Session = Depends(get_db)):
    return db.scalars(select(models.Qualification).order_by(models.Qualification.order)).all()


@router.get("/{qualification_id}", response_model=schemas.QualificationOut)
def get_qualification(qualification_id: int, db: Session = Depends(get_db)):
    qualification = db.get(models.Qualification, qualification_id)
    if not qualification:
        raise HTTPException(status_code=404, detail="Qualification not found")
    return qualification


@router.post("", response_model=schemas.QualificationOut, dependencies=[Depends(require_admin_session)])
def create_qualification(payload: schemas.QualificationCreate, db: Session = Depends(get_db)):
    qualification = models.Qualification(**payload.model_dump())
    db.add(qualification)
    db.commit()
    db.refresh(qualification)
    return qualification


@router.put("/{qualification_id}", response_model=schemas.QualificationOut, dependencies=[Depends(require_admin_session)])
def update_qualification(qualification_id: int, payload: schemas.QualificationUpdate, db: Session = Depends(get_db)):
    qualification = db.get(models.Qualification, qualification_id)
    if not qualification:
        raise HTTPException(status_code=404, detail="Qualification not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(qualification, field, value)
    db.commit()
    db.refresh(qualification)
    return qualification


@router.delete("/{qualification_id}", status_code=204, dependencies=[Depends(require_admin_session)])
def delete_qualification(qualification_id: int, db: Session = Depends(get_db)):
    qualification = db.get(models.Qualification, qualification_id)
    if not qualification:
        raise HTTPException(status_code=404, detail="Qualification not found")
    db.delete(qualification)
    db.commit()
