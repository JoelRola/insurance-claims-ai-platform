from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.models.review import FieldReview, ReviewTask

router = APIRouter(tags=["reviews"])


class Assignment(BaseModel):
    owner: str


class Completion(BaseModel):
    results: list[FieldReview]


@router.get("/reviews")
def list_reviews(request: Request):
    return [task.model_dump() for task in request.app.state.reviews.list()]


@router.post("/reviews/{review_id}/claim")
def claim_review(review_id: str, body: Assignment, request: Request):
    try:
        task = request.app.state.reviews.assign(review_id, body.owner)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="review_not_found") from exc
    request.app.state.audit.append("review_assigned", task.case_id, {"review_id": review_id, "owner": body.owner})
    return task.model_dump()


@router.post("/reviews/{review_id}/complete")
def complete_review(review_id: str, body: Completion, request: Request):
    try:
        task = request.app.state.reviews.complete(review_id, body.results)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="review_not_found") from exc
    request.app.state.audit.append("review_completed", task.case_id, {"review_id": review_id})
    for result in body.results:
        if result.outcome == "corrected":
            request.app.state.audit.append("field_corrected", task.case_id, {"field": result.field})
    return task.model_dump()

