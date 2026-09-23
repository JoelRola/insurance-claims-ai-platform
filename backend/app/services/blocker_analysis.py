from app.models.claim import Claim
from app.models.review import ReviewTask


def analyze_blockers(claim: Claim, reviews: list[ReviewTask]) -> list[str]:
    blockers = list(claim.blockers)
    for document in claim.documents:
        if document.status == "missing":
            blockers.append(f"Required document missing: {document.document_type}")
        elif document.status == "unreadable":
            blockers.append(f"Document unreadable: {document.document_type}")
    for review in reviews:
        for result in review.results:
            if result.outcome in {"illegible", "not_present", "unresolved"}:
                blockers.append(f"Human review unresolved: {result.field}")
    return list(dict.fromkeys(blockers))

