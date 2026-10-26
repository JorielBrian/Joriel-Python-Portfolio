"""Add the area field to existing skills without losing existing records.

Run once against the configured DATABASE_URL:
    python -m scripts.migrate_skill_area
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from app.database import engine


def main() -> None:
    with engine.begin() as connection:
        connection.execute(text(
            'ALTER TABLE skills ADD COLUMN IF NOT EXISTS area VARCHAR NOT NULL DEFAULT \'Other\''
        ))
    print("Skill area column is present; existing skills default to 'Other'.")


if __name__ == "__main__":
    main()
