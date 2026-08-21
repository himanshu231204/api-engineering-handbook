"""HTTP routes for the books resource."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BookNotFoundError, DuplicateIsbnError
from app.db.session import get_session
from app.repositories.book_repository import BookRepository
from app.schemas.book import (
    BookCreate,
    BookList,
    BookPatch,
    BookRead,
    BookUpdate,
    SortField,
    SortOrder,
)
from app.services.book_service import BookService
from app.core.config import settings

router = APIRouter(prefix="/books", tags=["books"])


def get_service(session: AsyncSession = Depends(get_session)) -> BookService:
    return BookService(BookRepository(session))


@router.post("", response_model=BookRead, status_code=status.HTTP_201_CREATED)
async def create_book(
    payload: BookCreate, response: Response, service: BookService = Depends(get_service)
) -> BookRead:
    try:
        book = await service.create_book(payload)
    except DuplicateIsbnError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    response.headers["Location"] = f"/books/{book.id}"
    return BookRead.model_validate(book)


@router.get("", response_model=BookList)
async def list_books(
    limit: int = Query(default=settings.default_page_limit, ge=1, le=settings.max_page_limit),
    offset: int = Query(default=0, ge=0),
    genre: Optional[str] = None,
    author: Optional[str] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    sort_by: SortField = "title",
    order: SortOrder = "asc",
    service: BookService = Depends(get_service),
) -> BookList:
    items, total = await service.list_books(
        limit=limit,
        offset=offset,
        genre=genre,
        author=author,
        year_from=year_from,
        year_to=year_to,
        sort_by=sort_by,
        order=order,
    )
    return BookList(
        items=[BookRead.model_validate(b) for b in items], total=total, limit=limit, offset=offset
    )


@router.get("/{book_id}", response_model=BookRead)
async def get_book(book_id: str, service: BookService = Depends(get_service)) -> BookRead:
    try:
        book = await service.get_book(book_id)
    except BookNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return BookRead.model_validate(book)


@router.put("/{book_id}", response_model=BookRead)
async def replace_book(
    book_id: str, payload: BookUpdate, service: BookService = Depends(get_service)
) -> BookRead:
    try:
        book = await service.replace_book(book_id, payload)
    except BookNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DuplicateIsbnError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return BookRead.model_validate(book)


@router.patch("/{book_id}", response_model=BookRead)
async def patch_book(
    book_id: str, payload: BookPatch, service: BookService = Depends(get_service)
) -> BookRead:
    try:
        book = await service.patch_book(book_id, payload)
    except BookNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DuplicateIsbnError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return BookRead.model_validate(book)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: str, service: BookService = Depends(get_service)) -> Response:
    await service.delete_book(book_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
