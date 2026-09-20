"""
Creates all tables (if they don't exist) and seeds them with your real
portfolio data, exported directly from the Next.js app/data/*.ts files
(so there's no risk of manual-retyping mistakes).

Usage:
    python -m scripts.seed
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import Base, engine, SessionLocal
from app import models

SEED_FILE = Path(__file__).parent / "seed_data.json"


def main():
    print(f"Connecting to: {os.environ['DATABASE_URL'].split('@')[-1]}")
    Base.metadata.create_all(bind=engine)
    print("Tables created (or already existed).")

    data = json.loads(SEED_FILE.read_text())
    db = SessionLocal()
    try:
        if db.query(models.Project).count() == 0:
            for i, p in enumerate(data["projects"]):
                db.add(models.Project(
                    name=p["name"], image=p["image"], link=p.get("link"),
                    description=p["description"], skills=p["skills"], order=i,
                ))
            print(f"Seeded {len(data['projects'])} projects.")
        else:
            print("Projects table not empty, skipping.")

        if db.query(models.Qualification).count() == 0:
            for i, q in enumerate(data["qualifications"]):
                db.add(models.Qualification(
                    title=q["title"], company=q["company"], date=q["date"],
                    contract=q["contract"], description=q["description"],
                    skills=q["skills"], order=i,
                ))
            print(f"Seeded {len(data['qualifications'])} qualifications.")
        else:
            print("Qualifications table not empty, skipping.")

        if db.query(models.Skill).count() == 0:
            for i, s in enumerate(data["skills"]):
                db.add(models.Skill(
                    skill=s["skill"], image=s["image"], focus=s.get("focus", False),
                    proficiency=s["proficiency"], preference=s["preference"],
                    category=s["category"], order=i,
                ))
            print(f"Seeded {len(data['skills'])} skills.")
        else:
            print("Skills table not empty, skipping.")

        if db.query(models.ContentBlock).count() == 0:
            for key, paragraphs in data["content"].items():
                db.add(models.ContentBlock(key=key, paragraphs=paragraphs))
            print(f"Seeded {len(data['content'])} content blocks.")
        else:
            print("Content blocks table not empty, skipping.")

        db.commit()
        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
