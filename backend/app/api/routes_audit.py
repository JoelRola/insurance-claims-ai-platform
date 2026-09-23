from fastapi import APIRouter, Request

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/{case_id}")
def get_audit(case_id: str, request: Request):
    return request.app.state.audit.for_case(case_id)

