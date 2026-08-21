import pytest

VALID_BOOK = {
    "title": "The Pragmatic Programmer",
    "author": "David Thomas",
    "isbn": "9780135957059",
    "genre": "Software Engineering",
    "published_year": 2019,
    "page_count": 352,
    "rating": 4.5,
}


@pytest.mark.asyncio
async def test_create_book_success(client):
    resp = await client.post("/books", json=VALID_BOOK)
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == VALID_BOOK["title"]
    assert body["isbn"] == VALID_BOOK["isbn"]
    assert "id" in body
    assert resp.headers["location"] == f"/books/{body['id']}"


@pytest.mark.asyncio
async def test_create_book_duplicate_isbn_conflicts(client):
    await client.post("/books", json=VALID_BOOK)
    resp = await client.post("/books", json=VALID_BOOK)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_book_invalid_isbn_rejected(client):
    payload = {**VALID_BOOK, "isbn": "not-an-isbn"}
    resp = await client.post("/books", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_book_negative_page_count_rejected(client):
    payload = {**VALID_BOOK, "isbn": "9780132350884", "page_count": -5}
    resp = await client.post("/books", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_book_rating_out_of_range_rejected(client):
    payload = {**VALID_BOOK, "isbn": "9780132350884", "rating": 7}
    resp = await client.post("/books", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_book_blank_title_rejected(client):
    payload = {**VALID_BOOK, "isbn": "9780132350884", "title": "   "}
    resp = await client.post("/books", json=payload)
    assert resp.status_code == 422
