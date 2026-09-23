from typing import Literal

from pydantic import BaseModel, Field


Domain = Literal["auto", "work_accidents"]


class Document(BaseModel):
    document_id: str
    document_type: str
    status: Literal["present", "missing", "unreadable"]
    extracted_fields: dict[str, str] = Field(default_factory=dict)


class Claim(BaseModel):
    case_id: str
    process_number: str
    domain: Domain
    claimant_name: str
    employer_name: str | None = None
    workflow_stage: str
    readiness: Literal["complete", "incomplete", "review_required", "conflict"]
    official_status: str = "open"
    documents: list[Document] = Field(default_factory=list)
    structured_facts: dict[str, str] = Field(default_factory=dict)
    blockers: list[str] = Field(default_factory=list)
    recommendation: str

