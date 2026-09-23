from typing import Literal

from pydantic import BaseModel, Field


ReviewStatus = Literal["unassigned", "assigned", "in_progress", "completed"]
FieldOutcome = Literal["confirmed", "corrected", "illegible", "not_present", "not_applicable", "unresolved"]


class FieldReview(BaseModel):
    field: str
    outcome: FieldOutcome
    value: str = ""
    note: str = ""


class ReviewTask(BaseModel):
    review_id: str
    case_id: str
    status: ReviewStatus = "unassigned"
    owner: str | None = None
    fields: list[str] = Field(default_factory=list)
    results: list[FieldReview] = Field(default_factory=list)

