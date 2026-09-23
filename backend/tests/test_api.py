from fastapi.testclient import TestClient

from app.main import create_app


def test_health_and_claim_endpoints():
    client = TestClient(create_app())
    assert client.get("/health").json()["data_profile"] == "synthetic"
    assert client.get("/claims/AUTO-001").status_code == 200
    assert client.get("/claims/unknown").status_code == 404


def test_openapi_documents_public_routes():
    client = TestClient(create_app())
    schema = client.get("/openapi.json").json()
    assert "/health" in schema["paths"]
    assert "/decision-support/{case_id}/prepare" in schema["paths"]


def test_claim_list_contains_only_synthetic_cases():
    client = TestClient(create_app())
    rows = client.get("/claims").json()
    assert len(rows) == 6
    assert all(row["case_id"].startswith(("AUTO-", "AT-")) for row in rows)


def test_analysis_and_audit():
    client = TestClient(create_app())
    response = client.post("/assistant/analyze/AUTO-001")
    assert response.status_code == 200
    assert response.json()["status"] == "awaiting_human_review"
    assert client.get("/audit/AUTO-001").json()[0]["event_type"] == "case_analysis_created"


def test_review_claim_and_complete_endpoints():
    client = TestClient(create_app())
    reviews = client.get("/reviews").json()
    assert reviews
    review_id = reviews[0]["review_id"]
    assert client.post(f"/reviews/{review_id}/claim", json={"owner": "synthetic-reviewer"}).status_code == 200
    response = client.post(f"/reviews/{review_id}/complete", json={"results": [{"field": reviews[0]["fields"][0], "outcome": "confirmed", "value": "synthetic"}]})
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


def test_ready_handoff_review_does_not_approve_claim():
    client = TestClient(create_app())
    prepared = client.post("/decision-support/AUTO-001/prepare")
    assert prepared.status_code == 200
    handoff = client.get("/decision-support/AUTO-001").json()
    assert handoff["status"] == "ready_for_decision"
    reviewed = client.post("/decision-support/AUTO-001", json={"action": "agree", "reviewer": "synthetic-manager"})
    assert reviewed.status_code == 200
    assert reviewed.json()["status"] == "reviewed"
    assert client.get("/claims/AUTO-001").json()["official_status"] == "open"


def test_handoff_disagreement_and_return_are_internal():
    client = TestClient(create_app())
    assert client.post("/decision-support/AUTO-001/prepare").status_code == 200
    disagreement = client.post("/decision-support/AUTO-001", json={"action": "disagree", "reviewer": "synthetic-manager", "note": "Needs review"})
    assert disagreement.json()["status"] == "reviewed"
    assert disagreement.json()["review_action"] == "disagree"
    assert client.get("/claims/AUTO-001").json()["official_status"] == "open"


def test_handoff_return_for_evidence_preserves_internal_status():
    client = TestClient(create_app())
    client.post("/decision-support/AT-002/prepare")
    returned = client.post("/decision-support/AT-002", json={"action": "return_for_evidence", "reviewer": "synthetic-manager", "note": "Check document"})
    assert returned.status_code == 200
    assert returned.json()["status"] == "returned_for_evidence"


def test_audit_history_is_append_only_for_analysis_and_handoff():
    client = TestClient(create_app())
    client.post("/assistant/analyze/AUTO-001")
    client.post("/decision-support/AUTO-001/prepare")
    events = client.get("/audit/AUTO-001").json()
    assert [event["event_type"] for event in events] == ["case_analysis_created", "decision_handoff_created"]


def test_incomplete_handoff_is_blocked():
    client = TestClient(create_app())
    assert client.post("/decision-support/AUTO-002/prepare").status_code == 409
