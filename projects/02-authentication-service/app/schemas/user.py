from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

_PASSWORD_RE = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,128}$")


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def _strength(cls, v: str) -> str:
        if not _PASSWORD_RE.match(v):
            raise ValueError(
                "password must be 8-128 characters and include an uppercase letter, "
                "a lowercase letter, and a digit"
            )
        return v


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    role: Literal["user", "admin"]
    is_verified: bool
    created_at: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    detail: str
    # Returned only for local dev/testing per the project spec -- a real
    # deployment emails this token instead of returning it in the response.
    reset_token: str | None = None


class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _strength(cls, v: str) -> str:
        if not _PASSWORD_RE.match(v):
            raise ValueError(
                "password must be 8-128 characters and include an uppercase letter, "
                "a lowercase letter, and a digit"
            )
        return v
