"""
Repository pattern: all data access for `Task` rows lives behind this one
class. Routers depend on `TaskRepository`, never on SQLAlchemy directly --
that keeps HTTP concerns (routers) and persistence concerns (repository)
from leaking into each other. See docs/04-databases-and-apis/repository-pattern.md.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import TaskNotFoundError
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


class TaskRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self, *, completed: bool | None, limit: int, offset: int) -> tuple[list[Task], int]:
        query = select(Task)
        count_query = select(func.count()).select_from(Task)

        if completed is not None:
            query = query.where(Task.completed == completed)
            count_query = count_query.where(Task.completed == completed)

        total = self.db.scalar(count_query) or 0
        rows = list(self.db.execute(query.order_by(Task.id).offset(offset).limit(limit)).scalars().all())
        return rows, total

    def get(self, task_id: int) -> Task:
        task = self.db.get(Task, task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        return task

    def create(self, data: TaskCreate) -> Task:
        # mode="json" turns the Priority enum into its plain string value,
        # matching the `priority: str` column -- avoids storing an Enum
        # instance in a String column.
        task = Task(**data.model_dump(mode="json"))
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def update(self, task_id: int, data: TaskUpdate) -> Task:
        task = self.get(task_id)
        # exclude_unset=True: only apply fields the client actually sent,
        # so PATCH stays a *partial* update instead of resetting omitted
        # fields to their schema defaults.
        for field, value in data.model_dump(mode="json", exclude_unset=True).items():
            setattr(task, field, value)
        self.db.commit()
        self.db.refresh(task)
        return task

    def delete(self, task_id: int) -> None:
        task = self.get(task_id)
        self.db.delete(task)
        self.db.commit()
