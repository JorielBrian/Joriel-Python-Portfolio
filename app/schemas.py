from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ProjectBase(BaseModel):
    name: str
    image: str
    link: str | None = None
    description: str
    skills: list[str] = []
    order: int = 0


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = None
    image: str | None = None
    link: str | None = None
    description: str | None = None
    skills: list[str] | None = None
    order: int | None = None


class ProjectOut(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class QualificationBase(BaseModel):
    title: str
    company: str
    date: str
    contract: str
    description: list[str] = []
    skills: list[str] = []
    order: int = 0


class QualificationCreate(QualificationBase):
    pass


class QualificationUpdate(BaseModel):
    title: str | None = None
    company: str | None = None
    date: str | None = None
    contract: str | None = None
    description: list[str] | None = None
    skills: list[str] | None = None
    order: int | None = None


class QualificationOut(QualificationBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class SkillBase(BaseModel):
    skill: str
    image: str
    focus: bool = False
    proficiency: str
    preference: str
    category: str
    area: str = "Other"
    order: int = 0


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    skill: str | None = None
    image: str | None = None
    focus: bool | None = None
    proficiency: str | None = None
    preference: str | None = None
    category: str | None = None
    area: str | None = None
    order: int | None = None


class SkillOut(SkillBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ContentBlockUpdate(BaseModel):
    paragraphs: list[str]


class ContentBlockOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    key: str
    paragraphs: list[str]


class ResumeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    url: str
    original_filename: str
    uploaded_at: datetime
