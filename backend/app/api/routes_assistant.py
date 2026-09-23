from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/analyze/{case_id}")
def analyze(case_id: str, request: Request):
    resolution = request.app.state.resolver.resolve(case_id)
    if resolution.status != "resolved":
        raise HTTPException(status_code=404 if resolution.status == "not_found" else 409, detail=resolution.status)
    result = request.app.state.agent.analyze(request.app.state.tools_for(resolution.claim))
    request.app.state.audit.append("case_analysis_created", resolution.claim.case_id, {"analysis_run_id": result["analysis_run_id"]})
    return result

