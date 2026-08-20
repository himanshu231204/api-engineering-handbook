"""
`/tasks` router.

Demonstrates dependency injection (DB session -> repository -> route
handler), query-parameter-driven pagination/filtering, and correct status
codes for each CRUD operation. See docs/03-building-apis/dependency-injection.md.
"""

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.repositories.task_repository import TaskRepository
from app.schemas.task import Pagination, TaskCreate, TaskListResponse, TaskRead, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_task_repository(db: Session = Depends(get_db)) -> TaskRepository:
    """A dependency that itself depends on another dependency (`get_db`).
    FastAPI resolves the whole chain automatically per request."""
    return TaskRepository(db)


@router.get("", response_model=TaskListResponse, summary="List tasks")
def list_tasks(
    completed: bool | None = Query(default=None, description="Filter by completion status"),
    offset: int = Query(default=0, ge=0),
    limit: int | None = Query(default=None, ge=1, description="Defaults to the server's page size"),
    repo: TaskRepository = Depends(get_task_repository),
    settings: Settings = Depends(get_settings),
) -> TaskListResponse:
    effective_limit = min(limit or settings.default_page_size, settings.max_page_size)
    tasks, total = repo.list(completed=completed, limit=effective_limit, offset=offset)
    next_offset = offset + effective_limit if offset + effective_limit < total else None

    return TaskListResponse(
        results=[TaskRead.model_validate(task) for task in tasks],
        pagination=Pagination(total=total, limit=effective_limit, offset=offset, next_offset=next_offset),
    )


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED, summary="Create a task")
def create_task(payload: TaskCreate, repo: TaskRepository = Depends(get_task_repository)) -> TaskRead:
    task = repo.create(payload)
    return TaskRead.model_validate(task)


@router.get("/{task_id}", response_model=TaskRead, summary="Get a task")
def get_task(task_id: int, repo: TaskRepository = Depends(get_task_repository)) -> TaskRead:
    task = repo.get(task_id)
    return TaskRead.model_validate(task)


@router.patch("/{task_id}", response_model=TaskRead, summary="Partially update a task")
def update_task(
    task_id: int, payload: TaskUpdate, repo: TaskRepository = Depends(get_task_repository)
) -> TaskRead:
    task = repo.update(task_id, payload)
    return TaskRead.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a task")
def delete_task(task_id: int, repo: TaskRepository = Depends(get_task_repository)) -> Response:
    repo.delete(task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
