from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "data"
SYNTHETIC_CLAIMS = DATA_ROOT / "synthetic_claims" / "claims.json"
KNOWLEDGE_BASE = DATA_ROOT / "mock_knowledge_base" / "knowledge.json"

