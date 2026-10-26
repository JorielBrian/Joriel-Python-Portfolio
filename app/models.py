from sqlalchemy import String, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from .database import Base


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    image: Mapped[str] = mapped_column(String, nullable=False)
    link: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    skills: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Qualification(Base):
    __tablename__ = "qualifications"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    company: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[str] = mapped_column(String, nullable=False)
    contract: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    skills: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Skill(Base):
    __tablename__ = "skills"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    skill: Mapped[str] = mapped_column(String, nullable=False)
    image: Mapped[str] = mapped_column(String, nullable=False)
    focus: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    proficiency: Mapped[str] = mapped_column(String, nullable=False)
    preference: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    area: Mapped[str] = mapped_column(String, nullable=False, default="Other", server_default="Other")
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class ContentBlock(Base):
    __tablename__ = "content_blocks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    paragraphs: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)


class AdminUser(Base):
    __tablename__ = "admin_users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)


class Resume(Base):
    """Single-row table: the current CV file, stored in Neon Storage.
    Each new upload replaces this row (and deletes the old stored object)."""
    __tablename__ = "resume"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    object_key: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    uploaded_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
