# Architecture

The public demo separates deterministic operational state, provenance-aware
evidence, controlled retrieval, a single read-only analysis agent, human
review, handoff and audit. The boundaries are deliberately explicit so a
future model cannot become the official claims authority by accident.

PostgreSQL is represented in Compose as a future persistence dependency; this
first pass uses small in-memory repositories to keep local tests deterministic.

## Component boundaries

- `repositories/` owns synthetic state and append-only audit events.
- `services/case_resolution.py` resolves exact IDs, process numbers and safe
  normalized prefixes; ambiguity is returned rather than guessed.
- `services/retrieval.py` searches only the fictional knowledge base.
- `agent/tools.py` exposes read-only operations to the single agent.
- `agent/claim_analysis_agent.py` produces a structured recommendation and
  stops at `HUMAN DECISION REQUIRED`.
- API routes expose the workflow without turning internal review into an
  official claim decision.

## Authority order

Structured operational state is authoritative for workflow facts. Trusted
human evidence is authoritative for corrected fields. Controlled reference
retrieval supplies context only. The agent synthesizes these inputs; it does
not create authority of its own.
