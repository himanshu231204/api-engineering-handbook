import pytest


async def _create(client, **overrides):
    payload = {
        "title": "Book Title",
        "author": "Author Name",
        "isbn": "9780132350884",
        "genre": "Fiction",
        "published_year": 2000,
        "page_count": 200,
        "rating": 3.0,
    }
    payload.update(overrides)
    resp = await client.post("/books", json=payload)
    assert resp.status_code == 201
    return resp.json()


@pytest.mark.asyncio
async def test_list_books_empty(client):
    resp = await client.get("/books")
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0


@pytest.mark.asyncio
async def test_list_books_pagination(client):
    for i in range(5):
        await _create(client, isbn=f"978013235088{i}", title=f"Book {i}")
    resp = await client.get("/books", params={"limit": 2, "offset": 0})
    body = resp.json()
    assert len(body["items"]) == 2
    assert body["total"] == 5
    assert body["limit"] == 2
    assert body["offset"] == 0


@pytest.mark.asyncio
async def test_list_books_filter_by_genre(client):
    await _create(client, isbn="9780132350801", genre="Fiction")
    await _create(client, isbn="9780132350802", genre="Nonfiction")
    resp = await client.get("/books", params={"genre": "Fiction"})
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["genre"] == "Fiction"


@pytest.mark.asyncio
async def test_list_books_filter_by_year_range(client):
    await _create(client, isbn="9780132350803", published_year=1990)
    await _create(client, isbn="9780132350804", published_year=2010)
    resp = await client.get("/books", params={"year_from": 2000, "year_to": 2020})
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["published_year"] == 2010


@pytest.mark.asyncio
async def test_list_books_sort_by_rating_desc(client):
    await _create(client, isbn="9780132350805", title="Low", rating=1.0)
    await _create(client, isbn="9780132350806", title="High", rating=5.0)
    resp = await client.get("/books", params={"sort_by": "rating", "order": "desc"})
    body = resp.json()
    assert body["items"][0]["title"] == "High"
