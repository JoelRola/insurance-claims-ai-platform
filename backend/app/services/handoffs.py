from datetime import datetime, timezone
from hashlib import sha256
from uuid import uuid4

from app.models.handoff import DecisionHandoff


class HandoffRepository:
    def __init__(self) -> None:
        self._rows: dict[str, DecisionHandoff] = {}

    def get_for_case(self, case_id: str) -> DecisionHandoff | None:
        return next((row for row in self._rows.values() if row.case_id == case_id), None)

    def prepare(self, case_id: str, recommendation: str, unresolved: list[str], analysis_run_id: str, evidence_snapshot: str, prepared_by: str) -> DecisionHandoff:
        current = self.get_for_case(case_id)
        if current and current.evidence_snapshot_id == evidence_snapshot and current.status != "returned_for_evidence":
            return current
        row = DecisionHandoff(handoff_id=current.handoff_id if current else str(uuid4()), case_id=case_id, status="ready_for_decision", prepared_by=prepared_by, prepared_at=datetime.now(timezone.utc).isoformat(), recommendation=recommendation, unresolved_items=unresolved, analysis_run_id=analysis_run_id, evidence_snapshot_id=evidence_snapshot)
        self._rows[row.handoff_id] = row
        return row

    def snapshot_id(self, analysis: dict[str, object]) -> str:
        return sha256(repr(sorted(analysis.items())).encode()).hexdigest()

    def review(self, handoff_id: str, action: str, reviewer: str, note: str = "") -> DecisionHandoff:
        row = self._rows[handoff_id]
        row.reviewed_by = reviewer
        row.reviewed_at = datetime.now(timezone.utc).isoformat()
        row.review_action = action
        row.review_note = note
        row.status = "returned_for_evidence" if action == "return_for_evidence" else "reviewed"
        return row

