"""Business rules for books: uniqueness checks, update semantics."""
from __future__ import annotations

from typing import Optional

from app.core.exceptions import BookNotFoundError, DuplicateIsbnError
from app.models.book import Book
from app.repositories.book_repository import BookRepository
from app.schemas.book import BookCreate, BookPatch, BookUpdate


class BookService:
    def __init__(self, repo: BookRepository) -> None:
        self._repo = repo

    async def create_book(self, payload: BookCreate) -> Book:
        existing = await self._repo.get_by_isbn(payload.isbn)
        if existing is not None:
            raise DuplicateIsbnError(payload.isbn)
        book = Book(**payload.model_dump())
        book = await self._repo.create(book)
        await self._repo.commit()
        return book

    async def get_book(self, book_id: str) -> Book:
        book = await self._repo.get(book_id)
        if book is None:
            raise BookNotFoundError(book_id)
        return book

    async def list_books(
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
    ) -> tuple[list[Book], int]:
        items = await self._repo.list(
            limit=limit,
            offset=offset,
            genre=genre,
            author=author,
            year_from=year_from,
            year_to=year_to,
            sort_by=sort_by,
            order=order,
        )
        total = await self._repo.count(genre=genre, author=author, year_from=year_from, year_to=year_to)
        return items, total

    async def replace_book(self, book_id: str, payload: BookUpdate) -> Book:
        book = await self.get_book(book_id)
        if payload.isbn != book.isbn:
            existing = await self._repo.get_by_isbn(payload.isbn)
            if existing is not None:
                raise DuplicateIsbnError(payload.isbn)
        for field, value in payload.model_dump().items():
            setattr(book, field, value)
        await self._repo.commit()
        return book

    async def patch_book(self, book_id: str, payload: BookPatch) -> Book:
        book = await self.get_book(book_id)
        updates = payload.model_dump(exclude_unset=True)
        if "isbn" in updates and updates["isbn"] != book.isbn:
            existing = await self._repo.get_by_isbn(updates["isbn"])
            if existing is not None:
                raise DuplicateIsbnError(updates["isbn"])
        for field, value in updates.items():
            setattr(book, field, value)
        await self._repo.commit()
        return book

    async def delete_book(self, book_id: str) -> None:
        """Idempotent delete: deleting a missing book is a silent no-op
        (204) rather than a 404 -- calling DELETE twice produces the same
        end state, which is the contract documented in this project's
        README."""
        book = await self._repo.get(book_id)
        if book is None:
            return
        await self._repo.delete(book)
        await self._repo.commit()
