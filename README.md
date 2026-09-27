# Institutional Evidence Tracker

> **Track evidence, provenance, decision ownership, dependencies, and next actions in multi-step administrative processes.**

Administrative processes often fail because evidence, ownership, dependencies, and next actions are scattered across messages and documents. This repository models those elements explicitly without embedding domain-specific legal conclusions.

## Implemented
- evidence objects with provenance
- verified/unverified evidence state
- decision-owner tracking
- required-evidence IDs
- blocking dependencies
- dependency resolution
- WAITING_OWNER/BLOCKED/WAITING_EVIDENCE/READY/COMPLETE states
- next-action calculation
- audit history

## Run
```bash
python -m unittest discover -s tests -v
python institutional_evidence_tracker.py
```

## Repository map
- `institutional_evidence_tracker.py` — core implementation
- `tests/` — deterministic tests
- `examples/` — reproducible example
- `docs/architecture.md` — architecture
- `docs/research-agenda.md` — experiments and research lineage
- `STATUS.md` — claims boundary
- `CITATION.cff` — citation metadata

## Pipeline
**case → decision owner → dependencies → required evidence → verification → status → next action**

## Research lineage
This is a generalized evidence-tracing artifact informed by long administrative/document workflows and the broader AI-governance interest in provenance, human ownership, accountability, and escalation.

## Evaluation direction
Generate synthetic institutional cases with missing owners, unresolved dependencies, unverified evidence, and completion states. Measure status correctness and ability to reconstruct why a case is blocked.

## Maturity
**Research prototype.** Generic administrative workflow software only. It is not legal advice, a case-management system used by any institution, or evidence that any real authority follows these states.
