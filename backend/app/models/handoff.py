from typing import Literal

from pydantic import BaseModel, Field


HandoffStatus = Literal["draft", "ready_for_decision", "under_human_review", "reviewed", "returned_for_evidence"]


class DecisionHandoff(BaseModel):
    handoff_id: str
    case_id: str
    status: HandoffStatus
    prepared_by: str
    prepared_at: str
    reviewed_by: str | None = None
    reviewed_at: str | None = None
    recommendation: str
    unresolved_items: list[str] = Field(default_factory=list)
    analysis_run_id: str
    evidence_snapshot_id: str
    review_action: str | None = None
    review_note: str | None = None

