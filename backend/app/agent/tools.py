from app.models.claim import Claim
from app.repositories.evidence import EvidenceRepository
from app.repositories.reviews import ReviewsRepository
from app.services.blocker_analysis import analyze_blockers


class ReadOnlyAgentTools:
    def __init__(self, claim: Claim, evidence: EvidenceRepository, reviews: ReviewsRepository) -> None:
        self.claim = claim
        self.evidence = evidence
        self.reviews = reviews

    def get_case(self) -> Claim:
        return self.claim

    def get_case_documents(self):
        return self.claim.documents

    def get_missing_documents(self) -> list[str]:
        return [doc.document_type for doc in self.claim.documents if doc.status == "missing"]

    def get_trusted_evidence(self):
        return self.evidence.effective(self.claim.case_id)

    def get_blockers(self) -> list[str]:
        return analyze_blockers(self.claim, [review for review in self.reviews.list() if review.case_id == self.claim.case_id])

    def get_review_status(self):
        return [review for review in self.reviews.list() if review.case_id == self.claim.case_id]

    def get_applicable_reference(self, retriever):
        return retriever.search("evidence review handoff")

    def draft_case_summary(self) -> str:
        return f"{self.claim.case_id}: {self.claim.claimant_name}; stage={self.claim.workflow_stage}; readiness={self.claim.readiness}."

