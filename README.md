# Institutional Evidence Tracker

<p align="center"><strong>Evidence Before Institutional Decision</strong><br/><sub>Track required evidence, verification, dependencies and accountable next actions.</sub></p>

<p align="center"><img src="https://img.shields.io/badge/status-reproducible%20prototype-blue" alt="Prototype"/> <img src="https://img.shields.io/badge/focus-evidence%20governance-orange" alt="Evidence governance"/></p>

## Question

**How can an institutional workflow make it obvious what evidence exists, what remains unverified, and who owns the next decision?**

```
Case
 ↓
Required evidence
 ↓
Evidence + provenance
 ↓
Verification
 ↓
Blocking dependencies
 ↓
Status + accountable next action
```

## Try it

```bash
python institutional_evidence_tracker.py
python -m unittest discover -s tests -v
```

`evidence_packet.py` exports a deterministic, hash-fingerprinted evidence packet containing evidence state, dependencies, status, next action and audit history.

## Implemented

- institutional case state
- required-evidence tracking
- provenance
- verification state
- blocking dependencies
- accountable decision owner
- audit history
- deterministic evidence packet
- SHA-256 packet fingerprint
- deterministic CI

## Why it matters

This repository extends the portfolio's central idea beyond AI agents: **important decisions should expose their evidence state rather than hiding uncertainty behind a polished interface.**

Related: [Agent Evidence Probes](https://github.com/Hafiz-IIT/agent-evidence-probes) · [Agency QA Orchestrator](https://github.com/Hafiz-IIT/agency-qa-orchestrator) · [~haf.s__ OS Core](https://github.com/Hafiz-IIT/hafs-os-core)

## Boundary

Prototype institutional workflow infrastructure. It does not claim deployment inside a government, university, hospital or other institution.
