# Evaluation

## System consistency

System consistency asks whether the assistant matches the structured facts
already held by the application. Examples include resolving `AUTO-001`,
reporting that `AUTO-002` is missing photo evidence, and refusing to prepare a
handoff while blockers remain.

## Source truth

Source truth asks whether the structured facts themselves are correct relative
to original source documents. This is a different problem. A deterministic
system can be internally consistent while faithfully repeating a bad OCR
value. Human adjudication and provenance review are therefore required before
operational decisions.

## Synthetic evaluation story

The acceptance suite covers six invented claims, exact and ambiguous
resolution, missing versus unreadable evidence, evidence precedence, review
lifecycle, controlled retrieval, agent safety, handoff behavior and API
contracts. These are synthetic engineering metrics, not commercial or private
evaluation results.

