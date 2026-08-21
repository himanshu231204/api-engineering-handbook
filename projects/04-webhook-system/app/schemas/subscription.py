from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

# Loopback / link-local / private ranges blocked to reduce SSRF risk on a
# customer-supplied target_url. Not exhaustive -- a production deployment
# should resolve the hostname and check the resulting IP too.
_BLOCKED_HOST_PREFIXES = ("127.", "10.", "192.168.", "0.", "169.254.")
_BLOCKED_HOSTS = {"localhost"}


def _validate_target_url(url: str) -> str:
    parsed = HttpUrl(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("target_url must be http(s)")
    host = parsed.host or ""
    if host in _BLOCKED_HOSTS or any(host.startswith(p) for p in _BLOCKED_HOST_PREFIXES) or host.startswith("172."):
        raise ValueError("target_url must not point at a private/internal address")
    return url


class SubscriptionCreate(BaseModel):
    customer_id: str = Field(min_length=1)
    target_url: str
    event_types: list[str] = Field(min_length=1)

    @field_validator("target_url")
    @classmethod
    def _target_url(cls, v: str) -> str:
        return _validate_target_url(v)


class SubscriptionUpdate(BaseModel):
    target_url: Optional[str] = None
    event_types: Optional[list[str]] = None
    status: Optional[Literal["active", "paused"]] = None

    @field_validator("target_url")
    @classmethod
    def _target_url(cls, v: Optional[str]) -> Optional[str]:
        return _validate_target_url(v) if v is not None else v


class SubscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    target_url: str
    event_types: list[str]
    status: Literal["active", "paused"]
    created_at: datetime


class SubscriptionCreated(SubscriptionRead):
    # Shown once, at creation time, exactly like the README specifies.
    signing_secret: str


class SecretRotated(BaseModel):
    signing_secret: str
    previous_secret_valid_until: datetime
