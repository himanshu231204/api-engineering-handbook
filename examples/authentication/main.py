"""
JWT access/refresh token authentication in FastAPI.

Demonstrates: registering a user with a hashed password, logging in to
receive an access token + refresh token, a route protected by a valid
access token, and a refresh endpoint that trades a refresh token for a new
access token. See:
docs/05-authentication-authorization/jwt-deeply-explained.md
docs/05-authentication-authorization/access-vs-refresh-tokens.md
docs/05-authentication-authorization/bearer-tokens.md

Storage is a plain in-memory dict -- the point of this example is the auth
flow, not persistence (see examples/fastapi-crud for a real repository
layer).

Run it:
    uvicorn main:app --reload
"""

from __future__ import annotations

import os
import secrets
import sys
from datetime import datetime, timedelta, timezone
from typing import Literal

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Configuration -- read from environment variables (and, in development, a
# local .env file). Never hardcode a real signing secret. See .env.example.
# ---------------------------------------------------------------------------

load_dotenv()

_secret_from_env = os.environ.get("JWT_SECRET_KEY")
if _secret_from_env:
    JWT_SECRET_KEY = _secret_from_env
else:
    # Falls back to a random secret so the example still runs out of the
    # box, but tokens won't survive a restart and this must never happen
    # in production -- always set JWT_SECRET_KEY explicitly there.
    JWT_SECRET_KEY = secrets.token_hex(32)
    print(
        "WARNING: JWT_SECRET_KEY is not set. Using a random, process-only "
        "secret (see .env.example). This is fine for trying the example, "
        "never do this in production.",
        file=sys.stderr,
    )

JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=True, description="Paste an access token from /login")

# ---------------------------------------------------------------------------
# "Database" -- in-memory only.
# ---------------------------------------------------------------------------


class UserRecord(BaseModel):
    username: str
    hashed_password: str


_users: dict[str, UserRecord] = {}

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    username: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# JWT issuance / verification
# ---------------------------------------------------------------------------


def _create_token(*, subject: str, token_type: Literal["access", "refresh"], expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    claims = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(claims, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_access_token(username: str) -> str:
    return _create_token(
        subject=username, token_type="access", expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )


def create_refresh_token(username: str) -> str:
    return _create_token(
        subject=username, token_type="refresh", expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )


def decode_token(token: str, *, expected_type: Literal["access", "refresh"]) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        ) from exc

    if payload.get("type") != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Expected a {expected_type} token, got a {payload.get('type')} token",
        )
    return payload


def get_current_username(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    """FastAPI dependency: validates the `Authorization: Bearer <token>`
    header and returns the authenticated username, or raises 401."""
    payload = decode_token(credentials.credentials, expected_type="access")
    username = payload.get("sub")
    if username not in _users:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
    return username


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

app = FastAPI(title="JWT Authentication Example", version="1.0.0")


@app.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate) -> UserOut:
    if payload.username in _users:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already registered")
    _users[payload.username] = UserRecord(
        username=payload.username, hashed_password=hash_password(payload.password)
    )
    return UserOut(username=payload.username)


@app.post("/login", response_model=TokenPair)
def login(payload: LoginRequest) -> TokenPair:
    user = _users.get(payload.username)
    # Deliberately identical error for "no such user" and "wrong password"
    # -- don't let a login endpoint reveal which usernames exist.
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    return TokenPair(
        access_token=create_access_token(user.username),
        refresh_token=create_refresh_token(user.username),
    )


@app.post("/refresh", response_model=AccessTokenResponse)
def refresh(payload: RefreshRequest) -> AccessTokenResponse:
    """Trade a valid refresh token for a new access token, without making
    the client log in again. The refresh token itself is NOT rotated here
    for simplicity -- see the "Things to try" section in the README."""
    token_payload = decode_token(payload.refresh_token, expected_type="refresh")
    username = token_payload.get("sub")
    if username not in _users:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
    return AccessTokenResponse(access_token=create_access_token(username))


@app.get("/me", response_model=UserOut)
def read_current_user(username: str = Depends(get_current_username)) -> UserOut:
    """A protected route -- reachable only with a valid, non-expired access token."""
    return UserOut(username=username)
