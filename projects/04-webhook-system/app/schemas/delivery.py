from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class DeliveryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    subscription_id: str
    event_id: str
    status: Literal["pending", "delivered", "retrying", "failed", "dead_letter"]
    attempt_count: int
    max_attempts: int
    next_attempt_at: Optional[datetime]
    last_status_code: Optional[int]
    last_error: Optional[str]
    created_at: datetime
    updated_at: datetime


class DeliveryList(BaseModel):
    items: list[DeliveryRead]
    total: int
    limit: int
    offset: int


class DeliveryAttemptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    attempt_number: int
    status_code: Optional[int]
    response_snippet: Optional[str]
    error: Optional[str]
    attempted_at: datetime


class DeliveryDetail(DeliveryRead):
    attempts: list[DeliveryAttemptRead]


class InboundEventCreate(BaseModel):
    provider_event_id: str
    payload: dict


class InboundEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source: str
    provider_event_id: str
    signature_valid: bool
    processed_at: Optional[datetime]
    received_at: datetime


class OutboundEventCreate(BaseModel):
    event_type: str
    payload: dict
