from datetime import datetime, timezone
from typing import Any


class AuditRepository:
    """Append-only in-memory audit log for the demo process."""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def append(self, event_type: str, case_id: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        event = {"event_type": event_type, "case_id": case_id, "timestamp": datetime.now(timezone.utc).isoformat(), "metadata": metadata or {}}
        self.events.append(event)
        return event

    def for_case(self, case_id: str) -> list[dict[str, Any]]:
        return [event for event in self.events if event["case_id"] == case_id]

