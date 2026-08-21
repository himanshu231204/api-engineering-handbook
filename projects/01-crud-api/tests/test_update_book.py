import pytest

CREATE_PAYLOAD = {
    "title": "Original Title",
    "author": "Original Author",
    "isbn": "9780132350884",
    "genre": "Fiction",
    "published_year": 2000,
    "page_count": 200,
    "rating": 3.0,
}


@pytest.mark.asyncio
async def test_put_replaces_book(client):
    created = (await client.post("/books", json=CREATE_PAYLOAD)).json()
    replacement = {**CREATE_PAYLOAD, "title": "New Title", "rating": 4.0}
    resp = await client.put(f"/books/{created['id']}", json=replacement)
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "New Title"
    assert body["rating"] == 4.0


@pytest.mark.asyncio
async def test_put_missing_book_returns_404(client):
    resp = await client.put("/books/does-not-exist", json=CREATE_PAYLOAD)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_put_incomplete_payload_returns_422(client):
    created = (await client.post("/books", json=CREATE_PAYLOAD)).json()
    resp = await client.put(f"/books/{created['id']}", json={"title": "Only Title"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_patch_updates_only_supplied_fields(client):
    created = (await client.post("/books", json=CREATE_PAYLOAD)).json()
    resp = await client.patch(f"/books/{created['id']}", json={"rating": 5.0})
    assert resp.status_code == 200
    body = resp.json()
    assert body["rating"] == 5.0
    assert body["title"] == CREATE_PAYLOAD["title"]


@pytest.mark.asyncio
async def test_patch_missing_book_returns_404(client):
    resp = await client.patch("/books/does-not-exist", json={"rating": 5.0})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_patch_to_existing_isbn_conflicts(client):
    first = (await client.post("/books", json=CREATE_PAYLOAD)).json()
    second_payload = {**CREATE_PAYLOAD, "isbn": "9780132350801"}
    second = (await client.post("/books", json=second_payload)).json()
    resp = await client.patch(f"/books/{second['id']}", json={"isbn": first["isbn"]})
    assert resp.status_code == 409
