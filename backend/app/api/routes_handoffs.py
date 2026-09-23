from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/decision-support", tags=["decision-support"])


class ReviewDecision(BaseModel):
    action: str
    reviewer: str
    note: str = ""


@router.get("/{case_id}")
def get_handoff(case_id: str, request: Request):
    handoff = request.app.state.handoffs.get_for_case(case_id)
    if not handoff:
        raise HTTPException(status_code=404, detail="handoff_not_found")
    return handoff.model_dump()


@router.post("/{case_id}/prepare")
def prepare_handoff(case_id: str, request: Request):
    resolution = request.app.state.resolver.resolve(case_id)
    if resolution.status != "resolved":
        raise HTTPException(status_code=404 if resolution.status == "not_found" else 409, detail=resolution.status)
    analysis = request.app.state.agent.analyze(request.app.state.tools_for(resolution.claim))
    blockers = list(analysis["recommendation"]["blockers"])
    if blockers:
        raise HTTPException(status_code=409, detail="evidence_review_required")
    handoff = request.app.state.handoffs.prepare(case_id=resolution.claim.case_id, recommendation=str(analysis["recommendation"]["label"]), unresolved=[], analysis_run_id=str(analysis["analysis_run_id"]), evidence_snapshot=request.app.state.handoffs.snapshot_id(analysis), prepared_by="synthetic-operator")
    request.app.state.audit.append("decision_handoff_created", case_id, {"handoff_id": handoff.handoff_id})
    return handoff.model_dump()


@router.post("/{case_id}")
def review_handoff(case_id: str, body: ReviewDecision, request: Request):
    handoff = request.app.state.handoffs.get_for_case(case_id)
    if not handoff:
        raise HTTPException(status_code=404, detail="handoff_not_found")
    if body.action not in {"agree", "disagree", "return_for_evidence"}:
        raise HTTPException(status_code=422, detail="invalid_review_action")
    result = request.app.state.handoffs.review(handoff.handoff_id, body.action, body.reviewer, body.note)
    request.app.state.audit.append("recommendation_reviewed", case_id, {"action": body.action})
    return result.model_dump()

