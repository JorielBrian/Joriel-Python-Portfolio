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


@router.get("/content-health")
def get_content_health(db: Session = Depends(get_db)):
    """Inspect stored portfolio content and report fields that need admin attention."""
    projects = db.scalars(select(models.Project).order_by(models.Project.order)).all()
    qualifications = db.scalars(
        select(models.Qualification).order_by(models.Qualification.order)
    ).all()
    skills = db.scalars(select(models.Skill).order_by(models.Skill.order)).all()
    content_blocks = db.scalars(
        select(models.ContentBlock).order_by(models.ContentBlock.key)
    ).all()
    resume_configured = (
        db.scalar(select(func.count()).select_from(models.Resume)) or 0
    ) > 0

    checks = []

    def add_check(
        check_id: str,
        label: str,
        href: str,
        findings: list[dict[str, str]],
        description: str,
    ) -> None:
        checks.append(
            {
                "id": check_id,
                "label": label,
                "href": href,
                "description": description,
                "count": len(findings),
                "status": "attention" if findings else "healthy",
                "findings": findings[:5],
            }
        )

    project_findings: list[dict[str, str]] = []
    for project in projects:
        label = project.name.strip() or f"Project #{project.id}"
        for field, value in (
            ("name", project.name),
            ("description", project.description),
            ("image", project.image),
        ):
            if not value or not value.strip():
                project_findings.append(
                    {"item": label, "field": field, "message": f"Missing {field}"}
                )
    add_check(
        "projects",
        "Project details",
        "/admin/projects",
        project_findings,
        "Projects should have a name, description, and image.",
    )

    qualification_findings: list[dict[str, str]] = []
    for item in qualifications:
        label = item.title.strip() or f"Qualification #{item.id}"
        for field, value in (
            ("title", item.title),
            ("company", item.company),
            ("date", item.date),
            ("contract", item.contract),
        ):
            if not value or not value.strip():
                qualification_findings.append(
                    {"item": label, "field": field, "message": f"Missing {field}"}
                )
        if not [entry for entry in item.description if entry and entry.strip()]:
            qualification_findings.append(
                {"item": label, "field": "description", "message": "No description text"}
            )
    add_check(
        "qualifications",
        "Qualification details",
        "/admin/qualifications",
        qualification_findings,
        "Experience and qualifications should include their key details and description.",
    )

    skill_findings: list[dict[str, str]] = []
    for item in skills:
        label = item.skill.strip() or f"Skill #{item.id}"
        for field, value in (
            ("skill", item.skill),
            ("image", item.image),
            ("category", item.category),
            ("proficiency", item.proficiency),
            ("preference", item.preference),
        ):
            if not value or not value.strip():
                skill_findings.append(
                    {"item": label, "field": field, "message": f"Missing {field}"}
                )
    add_check(
        "skills",
        "Skill details",
        "/admin/skills",
        skill_findings,
        "Skills should have a name, image, category, proficiency, and preference.",
    )

    content_findings: list[dict[str, str]] = []
    for block in content_blocks:
        if not [paragraph for paragraph in block.paragraphs if paragraph and paragraph.strip()]:
            content_findings.append(
                {
                    "item": block.key,
                    "field": "paragraphs",
                    "message": "Content block has no text",
                }
            )
    add_check(
        "content",
        "Bio content",
        "/admin/content",
        content_findings,
        "Each saved content block should contain at least one non-empty paragraph.",
    )

    resume_findings = []
    if not resume_configured:
        resume_findings.append(
            {
                "item": "Résumé",
                "field": "file",
                "message": "No résumé record is configured",
            }
        )
    add_check(
        "resume",
        "Résumé",
        "/admin/content",
        resume_findings,
        "Checks whether a résumé record exists; it does not verify the file in storage.",
    )

    total_findings = sum(check["count"] for check in checks)
    return {
        "status": "attention" if total_findings else "healthy",
        "total_findings": total_findings,
        "checks": checks,
    }
