import pytest

CREATE_PAYLOAD = {
    "title": "Deletable Book",
    "author": "Author",
    "isbn": "9780132350884",
    "genre": "Fiction",
    "published_year": 2000,
    "page_count": 200,
    "rating": 3.0,
}


@pytest.mark.asyncio
async def test_delete_book_success(client):
    created = (await client.post("/books", json=CREATE_PAYLOAD)).json()
    resp = await client.delete(f"/books/{created['id']}")
    assert resp.status_code == 204

    follow_up = await client.get(f"/books/{created['id']}")
    assert follow_up.status_code == 404


@pytest.mark.asyncio
async def test_delete_is_idempotent(client):
    created = (await client.post("/books", json=CREATE_PAYLOAD)).json()
    first = await client.delete(f"/books/{created['id']}")
    second = await client.delete(f"/books/{created['id']}")
    assert first.status_code == 204
    assert second.status_code == 204


@pytest.mark.asyncio
async def test_delete_unknown_book_returns_204(client):
    resp = await client.delete("/books/never-existed")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_get_missing_book_returns_404(client):
    resp = await client.get("/books/never-existed")
    assert resp.status_code == 404
