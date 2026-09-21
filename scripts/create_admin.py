"""
Creates (or updates) the single admin user for dashboard login.
This is intentionally NOT an API endpoint — you run it yourself, once,
from your own machine, so nobody else can ever create an account.

Usage:
    python -m scripts.create_admin
"""
import sys
import getpass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.auth import hash_password
from app import models


def main():
    db = SessionLocal()
    try:
        username = input("Admin username: ").strip()
        if not username:
            print("Username can't be empty.")
            return

        password = getpass.getpass("Admin password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Passwords didn't match.")
            return
        if len(password) < 8:
            print("Use at least 8 characters.")
            return

        existing = db.query(models.AdminUser).filter_by(username=username).first()
        if existing:
            existing.password_hash = hash_password(password)
            db.commit()
            print(f"Updated password for existing user '{username}'.")
        else:
            user = models.AdminUser(username=username, password_hash=hash_password(password))
            db.add(user)
            db.commit()
            print(f"Created admin user '{username}'.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
