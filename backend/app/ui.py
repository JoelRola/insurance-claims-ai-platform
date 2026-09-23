from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import ROOT
from app.models.evidence import EvidenceRecord
from app.models.review import FieldReview, ReviewTask
from app.services.blocker_analysis import analyze_blockers


templates = Jinja2Templates(directory=str(ROOT / "frontend" / "templates"))
router = APIRouter(tags=["demo-ui"])


LABELS = {
    "auto": "Auto claim",
    "work_accidents": "Work accident",
    "complete": "Ready for human decision",
    "incomplete": "Evidence incomplete",
    "review_required": "Human review required",
    "conflict": "Evidence conflict",
    "open": "Open",
}


def label(value: object) -> str:
    return LABELS.get(str(value), str(value).replace("_", " ").title())


def _claim(request: Request, case_id: str):
    claim = request.app.state.claims.get(case_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Synthetic claim not found")
    return claim


def _evidence_rows(request: Request, claim) -> list[dict[str, object]]:
    effective = request.app.state.evidence.effective(claim.case_id)
    rows = []
    for field, value in claim.structured_facts.items():
        record = effective.get(field)
        rows.append({"field": field.replace("_", " ").title(), "value": record.value if record else value, "source": label(record.source_type) if record else "Structured", "source_type": record.source_type if record else "structured_system", "confidence": record.confidence if record else "structured"})
    unreadable = next((doc for doc in claim.documents if doc.status == "unreadable"), None)
    if unreadable:
        rows.append({"field": "Incident description", "value": "Partial value", "source": "OCR / unverified", "source_type": "ocr", "confidence": "unresolved"})
    return rows


def _analysis(request: Request, claim):
    result = request.app.state.analysis_runs.get(claim.case_id)
    if result is None:
        result = request.app.state.agent.analyze(request.app.state.tools_for(claim))
        request.app.state.analysis_runs[claim.case_id] = result
        request.app.state.audit.append("case_analysis_created", claim.case_id, {"analysis_run_id": result["analysis_run_id"]})
    return result


def _base(request: Request, **context):
    context.update({"request": request, "label": label, "product_name": "Insurance Claims AI Platform"})
    return context


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    claims = request.app.state.claims.list()
    return templates.TemplateResponse(request=request, name="home.html", context=_base(request, active="home", claims_count=len(claims), analysis_count=len(request.app.state.analysis_runs), review_count=len(request.app.state.reviews.list()), handoff_count=len(request.app.state.handoffs._rows)))


@router.get("/claims-ui", response_class=HTMLResponse)
def claim_list(request: Request, domain: str = "", status: str = ""):
    claims = request.app.state.claims.list()
    if domain in {"auto", "work_accidents"}:
        claims = [claim for claim in claims if claim.domain == domain]
    if status == "review":
        claims = [claim for claim in claims if claim.readiness in {"review_required", "conflict"}]
    if status == "ready":
        claims = [claim for claim in claims if claim.readiness == "complete"]
    rows = [{"claim": claim, "domain_label": label(claim.domain), "status_label": label(claim.readiness), "evidence_state": "Complete" if claim.readiness == "complete" else "Needs attention", "blocker_state": "No blockers" if not claim.blockers else f"{len(claim.blockers)} blocker(s)"} for claim in claims]
    return templates.TemplateResponse(request=request, name="claims.html", context=_base(request, active="claims", rows=rows, selected_domain=domain, selected_status=status))


@router.get("/claims-ui/{case_id}", response_class=HTMLResponse)
def claim_detail(request: Request, case_id: str):
    claim = _claim(request, case_id)
    reviews = [review for review in request.app.state.reviews.list() if review.case_id == case_id]
    handoff = request.app.state.handoffs.get_for_case(case_id)
    return templates.TemplateResponse(request=request, name="claim_detail.html", context=_base(request, active="claims", claim=claim, evidence_rows=_evidence_rows(request, claim), reviews=reviews, handoff=handoff, blockers=analyze_blockers(claim, reviews)))


@router.post("/claims-ui/{case_id}/analyze")
def analyze_claim(request: Request, case_id: str):
    claim = _claim(request, case_id)
    _analysis(request, claim)
    return RedirectResponse(f"/claims-ui/{quote(case_id)}/analysis", status_code=303)


@router.get("/claims-ui/{case_id}/analysis", response_class=HTMLResponse)
def analysis_page(request: Request, case_id: str):
    claim = _claim(request, case_id)
    result = _analysis(request, claim)
    return templates.TemplateResponse(request=request, name="analysis.html", context=_base(request, active="claims", claim=claim, analysis=result))


@router.get("/claims-ui/{case_id}/review", response_class=HTMLResponse)
def review_page(request: Request, case_id: str, saved: str = ""):
    claim = _claim(request, case_id)
    tasks = [task for task in request.app.state.reviews.list() if task.case_id == case_id]
    task = tasks[0] if tasks else None
    return templates.TemplateResponse(request=request, name="review.html", context=_base(request, active="claims", claim=claim, task=task, saved=saved))


@router.post("/claims-ui/{case_id}/review")
async def review_action(request: Request, case_id: str, action: str = Form("take"), field: str = Form(""), outcome: str = Form("confirmed"), value: str = Form(""), note: str = Form("")):
    claim = _claim(request, case_id)
    task = next((item for item in request.app.state.reviews.list() if item.case_id == case_id), None)
    if not task:
        task = request.app.state.reviews.create(ReviewTask(review_id=f"REV-{case_id}", case_id=case_id, fields=[field or "accident_date"]))
    if action == "take":
        request.app.state.reviews.assign(task.review_id, "synthetic-reviewer")
        request.app.state.reviews.start(task.review_id)
        request.app.state.audit.append("review_assigned", case_id, {"review_id": task.review_id})
    elif action == "complete":
        field = field or task.fields[0]
        completed = request.app.state.reviews.complete(task.review_id, [FieldReview(field=field, outcome=outcome, value=value, note=note)])
        if outcome in {"confirmed", "corrected"} and value.strip():
            source = "human_corrected" if outcome == "corrected" else "human_verified"
            request.app.state.evidence.add(EvidenceRecord(evidence_id=f"UI-{case_id}-{field}", case_id=case_id, field=field, value=value, source_type=source, confidence="verified", document_id=None, recorded_at=datetime.now(timezone.utc)))
            if outcome == "corrected":
                request.app.state.audit.append("field_corrected", case_id, {"field": field})
        request.app.state.audit.append("review_completed", case_id, {"review_id": completed.review_id})
    return RedirectResponse(f"/claims-ui/{quote(case_id)}/review?saved=1", status_code=303)


@router.get("/claims-ui/{case_id}/decision", response_class=HTMLResponse)
def decision_page(request: Request, case_id: str, message: str = ""):
    claim = _claim(request, case_id)
    handoff = request.app.state.handoffs.get_for_case(case_id)
    reviews = [review for review in request.app.state.reviews.list() if review.case_id == case_id]
    blockers = analyze_blockers(claim, reviews)
    return templates.TemplateResponse(request=request, name="decision.html", context=_base(request, active="claims", claim=claim, handoff=handoff, blockers=blockers, message=message))


@router.post("/claims-ui/{case_id}/decision")
async def decision_action(request: Request, case_id: str, action: str = Form("prepare"), note: str = Form("")):
    claim = _claim(request, case_id)
    if action == "prepare":
        analysis = _analysis(request, claim)
        if analysis["recommendation"]["blockers"]:
            return RedirectResponse(f"/claims-ui/{quote(case_id)}/decision?message=Evidence+review+required+before+handoff", status_code=303)
        handoff = request.app.state.handoffs.prepare(case_id, str(analysis["recommendation"]["label"]), [], str(analysis["analysis_run_id"]), request.app.state.handoffs.snapshot_id(analysis), "synthetic-operator")
        request.app.state.audit.append("decision_handoff_created", case_id, {"handoff_id": handoff.handoff_id})
    else:
        handoff = request.app.state.handoffs.get_for_case(case_id)
        if handoff:
            updated = request.app.state.handoffs.review(handoff.handoff_id, action, "synthetic-manager", note)
            request.app.state.audit.append("recommendation_reviewed", case_id, {"action": action, "handoff_id": updated.handoff_id})
    return RedirectResponse(f"/claims-ui/{quote(case_id)}/decision", status_code=303)


@router.get("/claims-ui/{case_id}/audit", response_class=HTMLResponse)
def audit_page(request: Request, case_id: str):
    claim = _claim(request, case_id)
    return templates.TemplateResponse(request=request, name="audit.html", context=_base(request, active="claims", claim=claim, events=request.app.state.audit.for_case(case_id)))


@router.get("/architecture", response_class=HTMLResponse)
def architecture_page(request: Request):
    return templates.TemplateResponse(request=request, name="architecture.html", context=_base(request, active="architecture"))


@router.get("/safety", response_class=HTMLResponse)
def safety_page(request: Request):
    return templates.TemplateResponse(request=request, name="safety.html", context=_base(request, active="safety"))

