"""
A small smoke-test suite for the `/tasks` API.

Not the focus of this example (see docs/13-api-testing/ for that), but
included so you have a working pattern for testing a FastAPI + SQLAlchemy
app: override the `get_db` dependency with an isolated in-memory SQLite
database instead of hitting the real `tasks.db` file.

Run with:
    pytest
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    # A fresh in-memory SQLite database per test, shared across connections
    # via StaticPool so it survives for the life of the test.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_and_get_task(client: TestClient) -> None:
    create_response = client.post("/tasks", json={"title": "Write tests", "priority": "high"})
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["title"] == "Write tests"
    assert created["completed"] is False

    get_response = client.get(f"/tasks/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == created["id"]


def test_list_tasks_pagination_shape(client: TestClient) -> None:
    for i in range(3):
        client.post("/tasks", json={"title": f"Task {i}"})

    response = client.get("/tasks", params={"limit": 2, "offset": 0})
    assert response.status_code == 200
    body = response.json()
    assert len(body["results"]) == 2
    assert body["pagination"]["total"] == 3
    assert body["pagination"]["next_offset"] == 2


def test_patch_is_partial(client: TestClient) -> None:
    created = client.post("/tasks", json={"title": "Original", "description": "keep me"}).json()

    patched = client.patch(f"/tasks/{created['id']}", json={"completed": True})
    assert patched.status_code == 200
    body = patched.json()
    assert body["completed"] is True
    assert body["title"] == "Original"
    assert body["description"] == "keep me"


def test_get_missing_task_returns_404_with_error_shape(client: TestClient) -> None:
    response = client.get("/tasks/999999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "task_not_found"


def test_delete_task(client: TestClient) -> None:
    created = client.post("/tasks", json={"title": "Delete me"}).json()
    delete_response = client.delete(f"/tasks/{created['id']}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/tasks/{created['id']}")
    assert get_response.status_code == 404
