"""Data-access layer for books -- the only place that talks SQLAlchemy."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book


class BookRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, book_id: str) -> Optional[Book]:
        return await self._session.get(Book, book_id)

    async def get_by_isbn(self, isbn: str) -> Optional[Book]:
        result = await self._session.execute(select(Book).where(Book.isbn == isbn))
        return result.scalar_one_or_none()

    def _filtered_query(
        self,
        *,
        genre: Optional[str],
        author: Optional[str],
        year_from: Optional[int],
        year_to: Optional[int],
    ) -> Select:
        query = select(Book)
        if genre:
            query = query.where(Book.genre == genre)
        if author:
            query = query.where(Book.author == author)
        if year_from is not None:
            query = query.where(Book.published_year >= year_from)
        if year_to is not None:
            query = query.where(Book.published_year <= year_to)
        return query

    async def count(
        self,
        *,
        genre: Optional[str] = None,
        author: Optional[str] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
    ) -> int:
        query = self._filtered_query(genre=genre, author=author, year_from=year_from, year_to=year_to)
        result = await self._session.execute(select(func.count()).select_from(query.subquery()))
        return int(result.scalar_one())

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        genre: Optional[str] = None,
        author: Optional[str] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        sort_by: str = "title",
        order: str = "asc",
    ) -> list[Book]:
        query = self._filtered_query(genre=genre, author=author, year_from=year_from, year_to=year_to)
        sort_column = getattr(Book, sort_by, Book.title)
        query = query.order_by(sort_column.desc() if order == "desc" else sort_column.asc())
        query = query.limit(limit).offset(offset)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(self, book: Book) -> Book:
        self._session.add(book)
        await self._session.flush()
        await self._session.refresh(book)
        return book

    async def delete(self, book: Book) -> None:
        await self._session.delete(book)

    async def commit(self) -> None:
        await self._session.commit()
