import os
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone

JWT_SECRET = os.environ["JWT_SECRET"]  # long random string, separate from ADMIN_API_KEY
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24 * 7  # a week; re-login after that

COOKIE_NAME = "admin_session"

# Locally, frontend (localhost:3000) and backend (localhost:8000) are still
# "same-site" (same registrable domain, different port), so Lax cookies work
# and don't require HTTPS. In production, frontend (vercel.app) and backend
# (onrender.com) are genuinely cross-site, which requires SameSite=None +
# Secure. Toggle with ENVIRONMENT=development in your local .env.
IS_PROD = os.environ.get("ENVIRONMENT", "production") != "development"
COOKIE_SECURE = IS_PROD
COOKIE_SAMESITE = "none" if IS_PROD else "lax"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_access_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """Returns the username if valid, None if missing/expired/tampered."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None
