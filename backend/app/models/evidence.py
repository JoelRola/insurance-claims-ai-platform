from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


SourceType = Literal["structured_system", "native_document", "ocr", "human_verified", "human_corrected"]


class EvidenceRecord(BaseModel):
    evidence_id: str
    case_id: str
    field: str
    value: str
    source_type: SourceType
    confidence: str
    document_id: str | None = None
    recorded_at: datetime


class EvidenceHistory(BaseModel):
    case_id: str
    records: list[EvidenceRecord] = Field(default_factory=list)

