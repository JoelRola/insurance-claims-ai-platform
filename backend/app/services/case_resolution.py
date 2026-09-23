import re
from dataclasses import dataclass

from app.repositories.claims import ClaimsRepository


@dataclass(frozen=True)
class Resolution:
    status: str
    claim: object | None = None
    candidates: list[str] | None = None


class CaseResolver:
    def __init__(self, claims: ClaimsRepository) -> None:
        self.claims = claims

    @staticmethod
    def normalize(value: str) -> str:
        return re.sub(r"[\s-]+", "-", value.strip().upper())

    def resolve(self, reference: str) -> Resolution:
        normalized = self.normalize(reference)
        exact = [claim for claim in self.claims.list() if self.normalize(claim.case_id) == normalized or self.normalize(claim.process_number) == normalized]
        if len(exact) == 1:
            return Resolution("resolved", exact[0])
        if len(exact) > 1:
            return Resolution("ambiguous", candidates=[claim.case_id for claim in exact])
        prefix = [claim for claim in self.claims.list() if self.normalize(claim.case_id).startswith(normalized + "-")]
        if len(prefix) == 1:
            return Resolution("resolved", prefix[0])
        if prefix:
            return Resolution("ambiguous", candidates=[claim.case_id for claim in prefix])
        return Resolution("not_found")

