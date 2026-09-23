from fastapi.testclient import TestClient

from app.main import create_app


def client():
    return TestClient(create_app())


def test_home_page_returns_200_with_synthetic_disclaimer():
    response = client().get("/")
    assert response.status_code == 200
    assert "Insurance Claims AI Platform" in response.text
    assert "Synthetic demo" in response.text


def test_claim_list_renders_synthetic_cases():
    response = client().get("/claims-ui")
    assert response.status_code == 200
    assert "AUTO-001" in response.text
    assert "AT-002" in response.text


def test_claim_list_filters_are_server_side():
    response = client().get("/claims-ui?domain=auto")
    assert "AUTO-001" in response.text
    assert "AT-001" not in response.text


def test_claim_detail_renders_provenance_labels():
    response = client().get("/claims-ui/AUTO-003")
    assert response.status_code == 200
    assert "TRUSTED EVIDENCE" in response.text
    assert "OCR / unverified" in response.text


def test_unknown_claim_is_safe_404():
    response = client().get("/claims-ui/UNKNOWN-999")
    assert response.status_code == 404
    assert "private" not in response.text.lower()


def test_analysis_page_renders_structured_result():
    response = client().get("/claims-ui/AUTO-003/analysis")
    assert response.status_code == 200
    assert "AI analysis" in response.text
    assert "Human decision required" in response.text
    assert "raw JSON" not in response.text


def test_human_review_page_renders_workflow():
    response = client().get("/claims-ui/AUTO-003/review")
    assert response.status_code == 200
    assert "Evidence review" in response.text
    assert "Complete review" in response.text
    assert "Correct" in response.text


def test_decision_support_page_has_safety_boundary():
    response = client().get("/claims-ui/AUTO-001/decision")
    assert response.status_code == 200
    assert "does not approve or reject" in response.text
    assert "Prepare for decision" in response.text


def test_audit_page_renders_timeline():
    response = client().get("/claims-ui/AUTO-001/audit")
    assert response.status_code == 200
    assert "Audit timeline" in response.text
    assert "Append-only" in response.text


def test_architecture_and_safety_pages_render():
    demo = client()
    assert demo.get("/architecture").status_code == 200
    assert "ClaimAnalysisAgent" in demo.get("/architecture").text
    safety = demo.get("/safety")
    assert safety.status_code == 200
    assert "THE AGENT CANNOT" in safety.text


def test_ui_has_no_external_action_urls_or_private_names():
    response = client().get("/claims-ui/AUTO-001")
    assert "http://" not in response.text
    assert "https://" not in response.text
    assert "Protteja" not in response.text
    assert "Mukua" not in response.text
