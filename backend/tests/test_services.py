from datetime import datetime, timezone

from app.agent.claim_analysis_agent import ClaimAnalysisAgent
from app.agent.tools import ReadOnlyAgentTools
from app.main import app
from app.models.evidence import EvidenceRecord
from app.services.case_resolution import CaseResolver


def test_exact_resolution_and_unknown_are_conservative():
    assert app.state.resolver.resolve("AUTO-001").status == "resolved"
    assert app.state.resolver.resolve("PROC-A-001").claim.case_id == "AUTO-001"
    assert app.state.resolver.resolve("AUTO-999").status == "not_found"


def test_resolution_normalizes_case_and_spacing():
    assert app.state.resolver.resolve(" auto 001 ").claim.case_id == "AUTO-001"


def test_resolution_does_not_use_unsafe_partial_fuzzy_matching():
    assert app.state.resolver.resolve("AUTO-00").status == "not_found"


def test_no_fuzzy_collision():
    result = app.state.resolver.resolve("AUTO")
    assert result.status == "ambiguous"


def test_trusted_evidence_precedence_and_history():
    repository = app.state.evidence.__class__()
    repository.add(EvidenceRecord(evidence_id="1", case_id="X", field="accident_date", value="ocr", source_type="ocr", confidence="low", recorded_at=datetime.now(timezone.utc)))
    repository.add(EvidenceRecord(evidence_id="2", case_id="X", field="accident_date", value="human", source_type="human_corrected", confidence="verified", recorded_at=datetime.now(timezone.utc)))
    assert repository.effective("X")["accident_date"].value == "human"
    assert len(repository.history("X")) == 2


def test_structured_evidence_is_available_before_human_review():
    claim = app.state.claims.get("AUTO-001")
    tools = ReadOnlyAgentTools(claim, app.state.evidence, app.state.reviews)
    assert tools.get_trusted_evidence()["accident_date"].source_type == "structured_system"


def test_human_review_outcomes_can_remain_unresolved():
    from app.models.review import FieldReview, ReviewTask
    reviews = app.state.reviews.__class__()
    task = reviews.create(ReviewTask(review_id="REV-X", case_id="X", fields=["date"]))
    reviews.assign(task.review_id, "synthetic-reviewer")
    reviews.start(task.review_id)
    completed = reviews.complete(task.review_id, [FieldReview(field="date", outcome="illegible")])
    assert completed.status == "completed"
    assert completed.results[0].outcome == "illegible"


def test_controlled_rag_returns_synthetic_reference():
    rows = app.state.retriever.search("human evidence review")
    assert rows
    assert rows[0]["reference_id"].startswith("KB-")


def test_rag_does_not_override_structured_readiness():
    claim = app.state.claims.get("AUTO-002")
    tools = ReadOnlyAgentTools(claim, app.state.evidence, app.state.reviews)
    result = ClaimAnalysisAgent(app.state.retriever).analyze(tools)
    assert claim.readiness == "incomplete"
    assert result["recommendation"]["blockers"]


def test_agent_is_structured_and_stops_before_decision():
    claim = app.state.claims.get("AUTO-002")
    result = ClaimAnalysisAgent(app.state.retriever).analyze(ReadOnlyAgentTools(claim, app.state.evidence, app.state.reviews))
    assert result["status"] == "awaiting_human_review"
    assert result["recommendation"]["blockers"]
    assert result["next_step"] == "HUMAN DECISION REQUIRED"
    assert "official claim state" in result["safety"]
    assert "official_status" not in result


def test_agent_tools_are_read_only():
    claim = app.state.claims.get("AUTO-001")
    tools = ReadOnlyAgentTools(claim, app.state.evidence, app.state.reviews)
    assert not hasattr(tools, "update_claim")
    assert tools.get_case().official_status == "open"


def test_agent_output_has_no_external_action_url():
    claim = app.state.claims.get("AUTO-001")
    result = ClaimAnalysisAgent(app.state.retriever).analyze(ReadOnlyAgentTools(claim, app.state.evidence, app.state.reviews))
    assert "http://" not in str(result)
    assert "https://" not in str(result)
