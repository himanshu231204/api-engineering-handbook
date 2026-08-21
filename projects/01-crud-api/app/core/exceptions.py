"""Domain-level exceptions, translated to HTTP responses in the routes layer."""
from __future__ import annotations


class BookNotFoundError(Exception):
    def __init__(self, book_id: str) -> None:
        self.book_id = book_id
        super().__init__(f"Book {book_id} not found")


class DuplicateIsbnError(Exception):
    def __init__(self, isbn: str) -> None:
        self.isbn = isbn
        super().__init__(f"Book with ISBN {isbn} already exists")
