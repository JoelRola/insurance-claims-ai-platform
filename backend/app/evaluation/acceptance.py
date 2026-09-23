from app.main import app


def run_acceptance() -> dict[str, bool]:
    claims = {claim.case_id: claim for claim in app.state.claims.list()}
    return {
        "synthetic_claim_count": len(claims) == 6,
        "incomplete_case_blocked": bool(claims["AUTO-002"].blockers),
        "complete_case_available": claims["AT-002"].readiness == "complete",
        "official_state_is_open": all(claim.official_status == "open" for claim in claims.values()),
    }

