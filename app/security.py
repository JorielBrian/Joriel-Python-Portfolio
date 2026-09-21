from fastapi import Request, HTTPException, status
from .auth import decode_access_token, COOKIE_NAME


def require_admin_session(request: Request):
    """Real auth for write endpoints, backed by the httpOnly session cookie
    set on login (see routers/auth.py). Replaces the old X-Admin-Key stopgap."""
    token = request.cookies.get(COOKIE_NAME)
    username = decode_access_token(token) if token else None
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please log in.",
        )
    return username
