def synthesize_recommendation(*, claim_status: str, blockers: list[str], references: list[dict[str, str]]) -> dict[str, object]:
    if blockers:
        label = "Review required before human decision"
    else:
        label = "Evidence supports human decision review"
    return {"label": label, "blockers": blockers, "references": references, "disclaimer": "Decision support only; a human remains the decision-maker."}

