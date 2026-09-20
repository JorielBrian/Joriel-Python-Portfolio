import os
from fastapi import Header, HTTPException, status


def require_admin_key(x_admin_key: str | None = Header(default=None)):
    """Temporary guard for write endpoints (POST/PUT/DELETE) until Phase 2 adds
    real session-based auth for the admin dashboard. Set ADMIN_API_KEY in the
    backend's environment, and send it as the X-Admin-Key header from any
    client allowed to write (for now, that's just you, testing manually or
    via the dashboard once it exists).
    """
    expected = os.environ.get("ADMIN_API_KEY")
    if not expected or x_admin_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid admin key",
        )
