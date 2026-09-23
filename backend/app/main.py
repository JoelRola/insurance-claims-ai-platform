from fastapi import FastAPI

from app.agent.claim_analysis_agent import ClaimAnalysisAgent
from app.agent.tools import ReadOnlyAgentTools
from app.api.routes_assistant import router as assistant_router
from app.api.routes_audit import router as audit_router
from app.api.routes_claims import router as claims_router
from app.api.routes_handoffs import router as handoff_router
from app.api.routes_health import router as health_router
from app.api.routes_reviews import router as reviews_router
from app.config import KNOWLEDGE_BASE, SYNTHETIC_CLAIMS
from app.repositories.audit import AuditRepository
from app.repositories.claims import ClaimsRepository
from app.repositories.evidence import EvidenceRepository
from app.repositories.reviews import ReviewsRepository
from app.services.case_resolution import CaseResolver
from app.services.handoffs import HandoffRepository
from app.services.retrieval import ControlledRetriever


def create_app() -> FastAPI:
    app = FastAPI(title="Insurance Claims AI Platform", version="0.1.0", description="Synthetic, auditable insurance claim decision support.")
    app.state.claims = ClaimsRepository(SYNTHETIC_CLAIMS)
    app.state.evidence = EvidenceRepository()
    app.state.reviews = ReviewsRepository()
    app.state.audit = AuditRepository()
    app.state.retriever = ControlledRetriever(KNOWLEDGE_BASE)
    app.state.resolver = CaseResolver(app.state.claims)
    app.state.handoffs = HandoffRepository()
    app.state.agent = ClaimAnalysisAgent(app.state.retriever)
    for claim in app.state.claims.list():
        for field, value in claim.structured_facts.items():
            from datetime import datetime, timezone
            from app.models.evidence import EvidenceRecord
            app.state.evidence.add(EvidenceRecord(evidence_id=f"E-{claim.case_id}-{field}", case_id=claim.case_id, field=field, value=value, source_type="structured_system", confidence="structured", recorded_at=datetime.now(timezone.utc)))
        for document in claim.documents:
            if document.status in {"unreadable", "present"} and claim.readiness in {"review_required", "conflict"}:
                from app.models.review import ReviewTask
                app.state.reviews.create(ReviewTask(review_id=f"REV-{claim.case_id}", case_id=claim.case_id, fields=list(claim.structured_facts)))
                break
    app.state.tools_for = lambda claim: ReadOnlyAgentTools(claim, app.state.evidence, app.state.reviews)
    app.include_router(health_router)
    app.include_router(claims_router)
    app.include_router(assistant_router)
    app.include_router(reviews_router)
    app.include_router(handoff_router)
    app.include_router(audit_router)
    return app


app = create_app()

