import json
from pathlib import Path


class ControlledRetriever:
    def __init__(self, path: Path) -> None:
        self._rows = json.loads(path.read_text(encoding="utf-8"))

    def search(self, query: str, limit: int = 3) -> list[dict[str, str]]:
        terms = {word.lower() for word in query.split() if len(word) > 3}
        scored = []
        for row in self._rows:
            text = f"{row['title']} {row['text']}".lower()
            score = sum(term in text for term in terms)
            if score:
                scored.append((score, row))
        return [row for _, row in sorted(scored, key=lambda item: item[0], reverse=True)[:limit]]

