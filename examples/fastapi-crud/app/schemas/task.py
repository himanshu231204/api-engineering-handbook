"""
Pydantic v2 request/response schemas for tasks.

Kept deliberately separate from the SQLAlchemy model in app/models/task.py
-- the API's shape and the database's shape are allowed to diverge, and
this is where that boundary lives. See
docs/03-building-apis/request-validation-pydantic.md and
docs/03-building-apis/response-models.md.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=200, examples=["Write the project README"])
    description: str | None = Field(default=None, max_length=2000)
    priority: Priority = Priority.medium


class TaskCreate(TaskBase):
    """Request body for POST /tasks."""


class TaskUpdate(BaseModel):
    """Request body for PATCH /tasks/{id}.

    Every field is optional: PATCH is a *partial* update, so only fields the
    client actually sent should be applied. The repository uses
    `model_dump(exclude_unset=True)` to tell "not sent" apart from
    "sent as null/False".
    """

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    priority: Priority | None = None
    completed: bool | None = None


class TaskRead(TaskBase):
    """Response body -- includes server-assigned fields the client can't set."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    completed: bool
    created_at: datetime
    updated_at: datetime


class Pagination(BaseModel):
    total: int
    limit: int
    offset: int
    next_offset: int | None = None


class TaskListResponse(BaseModel):
    """Every list endpoint in this API returns results + pagination
    metadata rather than a bare array -- see
    docs/02-rest-api-design/pagination.md."""

    results: list[TaskRead]
    pagination: Pagination
