from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from .. import models
from ..auth import (
    verify_password,
    create_access_token,
    decode_access_token,
    COOKIE_NAME,
    COOKIE_SECURE,
    COOKIE_SAMESITE,
    JWT_EXPIRE_HOURS,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(models.AdminUser).where(models.AdminUser.username == payload.username))
    if not user or not verify_password(payload.password, user.password_hash):
        # Same error for "no such user" and "wrong password" — don't reveal which.
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(user.username)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=JWT_EXPIRE_HOURS * 3600,
        path="/",
    )
    return {"username": user.username}


@router.post("/logout")
def logout(response: Response):
    # Browsers key a cookie on name + path + domain + the secure/samesite
    # attributes it was set with. delete_cookie() must match those exactly,
    # or the browser treats it as a different cookie and the original
    # session cookie silently survives — which is exactly what was
    # happening here before this fix.
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
    )
    return {"ok": True}


@router.get("/me")
def me(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    username = decode_access_token(token) if token else None
    if not username:
        raise HTTPException(status_code=401, detail="Not logged in")
    return {"username": username}
