from collections import defaultdict

from app.models.evidence import EvidenceRecord


PRECEDENCE = {"human_verified": 5, "human_corrected": 5, "structured_system": 4, "native_document": 3, "ocr": 2}


class EvidenceRepository:
    def __init__(self) -> None:
        self._records: list[EvidenceRecord] = []

    def add(self, record: EvidenceRecord) -> EvidenceRecord:
        self._records.append(record)
        return record

    def history(self, case_id: str) -> list[EvidenceRecord]:
        return [record for record in self._records if record.case_id == case_id]

    def effective(self, case_id: str) -> dict[str, EvidenceRecord]:
        effective: dict[str, EvidenceRecord] = {}
        for record in self.history(case_id):
            current = effective.get(record.field)
            if current is None or PRECEDENCE[record.source_type] >= PRECEDENCE[current.source_type]:
                effective[record.field] = record
        return effective

