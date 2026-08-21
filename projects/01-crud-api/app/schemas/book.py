"""Pydantic v2 request/response schemas for the books resource."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

_ISBN_RE = re.compile(r"^(?:\d{9}[\dXx]|\d{13})$")


def _validate_isbn(value: str) -> str:
    cleaned = value.replace("-", "").replace(" ", "")
    if not _ISBN_RE.match(cleaned):
        raise ValueError("isbn must be a valid ISBN-10 or ISBN-13 (digits, optional trailing X)")
    return cleaned


class BookBase(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    author: str = Field(min_length=1, max_length=300)
    isbn: str
    genre: str = Field(min_length=1, max_length=100)
    published_year: int = Field(ge=1450, le=2100)
    page_count: int = Field(gt=0)
    rating: float = Field(ge=0, le=5, default=0)

    @field_validator("isbn")
    @classmethod
    def _isbn(cls, v: str) -> str:
        return _validate_isbn(v)

    @field_validator("title", "author", "genre")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()


class BookCreate(BookBase):
    pass


class BookUpdate(BookBase):
    """Full replacement payload for PUT -- every field required."""


class BookPatch(BaseModel):
    """Partial update payload for PATCH -- every field optional."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    author: Optional[str] = Field(default=None, min_length=1, max_length=300)
    isbn: Optional[str] = None
    genre: Optional[str] = Field(default=None, min_length=1, max_length=100)
    published_year: Optional[int] = Field(default=None, ge=1450, le=2100)
    page_count: Optional[int] = Field(default=None, gt=0)
    rating: Optional[float] = Field(default=None, ge=0, le=5)

    @field_validator("isbn")
    @classmethod
    def _isbn(cls, v: Optional[str]) -> Optional[str]:
        return _validate_isbn(v) if v is not None else v


class BookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    author: str
    isbn: str
    genre: str
    published_year: int
    page_count: int
    rating: float
    created_at: datetime
    updated_at: datetime


class BookList(BaseModel):
    items: list[BookRead]
    total: int
    limit: int
    offset: int


SortField = Literal["title", "published_year", "rating"]
SortOrder = Literal["asc", "desc"]
