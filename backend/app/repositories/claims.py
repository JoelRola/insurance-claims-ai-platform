import json
from pathlib import Path

from app.models.claim import Claim


class ClaimsRepository:
    def __init__(self, path: Path) -> None:
        self._claims = [Claim.model_validate(row) for row in json.loads(path.read_text(encoding="utf-8"))]

    def list(self) -> list[Claim]:
        return list(self._claims)

    def get(self, case_id: str) -> Claim | None:
        return next((claim for claim in self._claims if claim.case_id == case_id), None)

