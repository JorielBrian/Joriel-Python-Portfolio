import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.environ["DATABASE_URL"]  # e.g. postgresql://user:pass@ep-xxxx.neon.tech/dbname?sslmode=require

# We use the psycopg3 driver (requirements.txt: psycopg[binary]). SQLAlchemy needs
# that spelled out in the URL scheme, but Neon gives you a plain postgresql:// or
# postgres:// string, so normalize it here rather than making you edit it by hand.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

# Neon works fine with a small pool; pool_pre_ping avoids stale-connection errors
# after the DB has been idle (Neon can suspend idle compute on the free tier).
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
