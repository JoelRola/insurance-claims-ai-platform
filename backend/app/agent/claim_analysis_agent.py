from uuid import uuid4

from app.agent.tools import ReadOnlyAgentTools
from app.services.response_synthesis import synthesize_recommendation


class ClaimAnalysisAgent:
    """One controlled, read-only analysis agent; it stops before official decision."""

    def __init__(self, retriever) -> None:
        self.retriever = retriever

    def analyze(self, tools: ReadOnlyAgentTools) -> dict[str, object]:
        claim = tools.get_case()
        blockers = tools.get_blockers()
        references = tools.get_applicable_reference(self.retriever) if blockers else []
        recommendation = synthesize_recommendation(claim_status=claim.readiness, blockers=blockers, references=references)
        return {
            "analysis_run_id": str(uuid4()),
            "case_id": claim.case_id,
            "status": "awaiting_human_review",
            "summary": tools.draft_case_summary(),
            "recommendation": recommendation,
            "trusted_evidence": [record.model_dump() for record in tools.get_trusted_evidence().values()],
            "human_review_status": [review.model_dump() for review in tools.get_review_status()],
            "next_step": "HUMAN DECISION REQUIRED",
            "safety": "Never approves, rejects, pays, emails, or changes official claim state.",
        }

