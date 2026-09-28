# Institutional Evidence Tracker

> Evidence/dependency tracker for multi-step institutional processes: provenance, decision owner, blocking dependencies, next action and audit.

## Status
**Reproducible prototype** with executable Python, tests, CI, architecture, evaluation and roadmap documentation.

## Problem
Administrative and institutional cases often stall because the current decision owner, unresolved dependency, or missing verified evidence is unclear. The tracker makes those dependencies explicit.

## Architecture
Case → decision owner → required evidence IDs → provenance/verification state → blocking dependencies → WAITING_OWNER / BLOCKED / WAITING_EVIDENCE / READY / COMPLETE → next action + audit.

## Run
```bash
python -m unittest discover -s tests -v
python institutional_evidence_tracker.py
```

## Implemented
- Decision-owner field
- Required evidence registry
- Evidence provenance and verification
- Blocking dependencies
- Status state machine
- Next-action calculation
- Audit trail
- Tests and CI

## Research lineage
- *The Future of Digital Trust: Secure Data Interactions in User-Centric Platforms*
- *Human-Centered AI Design for Inclusive Digital Platforms*
- *Ethical and Legal Dimensions of Autonomous Systems*

## Evaluation
Tests verify owner requirements, dependency blocking, verified-evidence readiness and terminal completion.

## Limitations
- Generic workflow model
- Not a legal-advice engine
- No institution integration
- No document-signature verification yet

## License
MIT.
