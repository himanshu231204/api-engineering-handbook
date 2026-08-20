"""
Domain-level exceptions.

Repositories and routers raise these without knowing anything about HTTP --
`app/main.py` registers an exception handler that translates them into the
right status code and JSON error shape. See
docs/03-building-apis/exception-handling.md.
"""


class TaskNotFoundError(Exception):
    def __init__(self, task_id: int):
        self.task_id = task_id
        super().__init__(f"Task {task_id} not found")
