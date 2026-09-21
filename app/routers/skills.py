from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import require_admin_session
from .. import models, schemas

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("", response_model=list[schemas.SkillOut])
def list_skills(db: Session = Depends(get_db)):
    return db.scalars(select(models.Skill).order_by(models.Skill.order)).all()


@router.get("/{skill_id}", response_model=schemas.SkillOut)
def get_skill(skill_id: int, db: Session = Depends(get_db)):
    skill = db.get(models.Skill, skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.post("", response_model=schemas.SkillOut, dependencies=[Depends(require_admin_session)])
def create_skill(payload: schemas.SkillCreate, db: Session = Depends(get_db)):
    skill = models.Skill(**payload.model_dump())
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


@router.put("/{skill_id}", response_model=schemas.SkillOut, dependencies=[Depends(require_admin_session)])
def update_skill(skill_id: int, payload: schemas.SkillUpdate, db: Session = Depends(get_db)):
    skill = db.get(models.Skill, skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(skill, field, value)
    db.commit()
    db.refresh(skill)
    return skill


@router.delete("/{skill_id}", status_code=204, dependencies=[Depends(require_admin_session)])
def delete_skill(skill_id: int, db: Session = Depends(get_db)):
    skill = db.get(models.Skill, skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    db.delete(skill)
    db.commit()
