from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/claims", tags=["claims"])


@router.get("")
def list_claims(request: Request):
    return [claim.model_dump() for claim in request.app.state.claims.list()]


@router.get("/{case_id}")
def get_claim(case_id: str, request: Request):
    claim = request.app.state.resolver.resolve(case_id)
    if claim.status != "resolved":
        raise HTTPException(status_code=404 if claim.status == "not_found" else 409, detail=claim.status)
    return claim.claim.model_dump()

