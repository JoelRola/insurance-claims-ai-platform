from __future__ import annotations

from app.models.review import FieldReview, ReviewTask


class ReviewsRepository:
    def __init__(self) -> None:
        self._tasks: dict[str, ReviewTask] = {}

    def create(self, task: ReviewTask) -> ReviewTask:
        self._tasks[task.review_id] = task
        return task

    def list(self) -> list[ReviewTask]:
        return list(self._tasks.values())

    def get(self, review_id: str) -> ReviewTask | None:
        return self._tasks.get(review_id)

    def assign(self, review_id: str, owner: str) -> ReviewTask:
        task = self._tasks[review_id]
        task.owner = owner
        task.status = "assigned"
        return task

    def start(self, review_id: str) -> ReviewTask:
        task = self._tasks[review_id]
        task.status = "in_progress"
        return task

    def complete(self, review_id: str, results: list[FieldReview]) -> ReviewTask:
        task = self._tasks[review_id]
        task.results = results
        task.status = "completed"
        return task
