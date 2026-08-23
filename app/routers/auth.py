import os
import secrets
import time
from datetime import datetime, timedelta
from urllib.parse import urlencode

import jwt
import requests as http_requests
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.dependencies import get_current_user, SESSION_SECRET, ALGORITHM

router = APIRouter(prefix="/auth", tags=["auth"])

# Short-lived, single-use codes so the session JWT never has to travel in a
# URL (browser history / server logs) — only this opaque code does, and it's
# worthless after one use or 60 seconds.
_EXCHANGE_CODE_TTL_SECONDS = 60
_pending_exchange_codes: dict[str, tuple[str, float]] = {}


def _create_exchange_code(session_token: str) -> str:
    code = secrets.token_urlsafe(32)
    _pending_exchange_codes[code] = (session_token, time.time() + _EXCHANGE_CODE_TTL_SECONDS)
    return code


def _consume_exchange_code(code: str) -> str | None:
    entry = _pending_exchange_codes.pop(code, None)
    if not entry:
        return None
    token, expires_at = entry
    if time.time() > expires_at:
        return None
    return token


class ExchangeCodeRequest(BaseModel):
    code: str


class ExchangeCodeResponse(BaseModel):
    token: str

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
FRONTEND_URL = os.getenv("FRONTEND_URL")
GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"


@router.get("/google/login")
def google_login():
    state = secrets.token_urlsafe(24)
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    response = RedirectResponse(f"{GOOGLE_AUTH_ENDPOINT}?{urlencode(params)}")
    response.set_cookie(
        "oauth_state", state, max_age=600, httponly=True, samesite="lax",
        secure=str(GOOGLE_REDIRECT_URI).startswith("https"),
    )
    return response


@router.get("/google/callback")
def google_callback(code: str, state: str, request: Request, db: Session = Depends(get_db)):
    if not state or state != request.cookies.get("oauth_state"):
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    token_res = http_requests.post(GOOGLE_TOKEN_ENDPOINT, data={
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    })
    if token_res.status_code != 200:
        raise HTTPException(status_code=400, detail="Google token exchange failed")

    claims = google_id_token.verify_oauth2_token(
        token_res.json()["id_token"], google_requests.Request(), GOOGLE_CLIENT_ID,
    )

    user = db.query(models.User).filter(models.User.google_sub == claims["sub"]).first()
    if not user:
        user = models.User(
            google_sub=claims["sub"],
            email=claims.get("email"),
            name=claims.get("name"),
            picture=claims.get("picture"),
        )
        db.add(user)
    else:
        user.email = claims.get("email") or user.email
        user.name = claims.get("name") or user.name
        user.picture = claims.get("picture") or user.picture
    db.commit()
    db.refresh(user)

    session_token = jwt.encode(
        {"sub": str(user.id), "exp": datetime.utcnow() + timedelta(days=30)},
        SESSION_SECRET, algorithm=ALGORITHM,
    )
    code = _create_exchange_code(session_token)
    response = RedirectResponse(f"{FRONTEND_URL}/auth/finish?code={code}")
    response.delete_cookie("oauth_state")
    return response


@router.post("/exchange", response_model=ExchangeCodeResponse)
def exchange_code(payload: ExchangeCodeRequest):
    token = _consume_exchange_code(payload.code)
    if not token:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    return ExchangeCodeResponse(token=token)


@router.get("/me", response_model=schemas.User)
def read_current_user(current_user: models.User = Depends(get_current_user)):
    return current_user
