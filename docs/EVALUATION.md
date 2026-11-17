# Evaluation

## Question
Can explicit evidence, owner and dependency state reduce ambiguity in long-running institutional processes?

## Metrics
- Missing-evidence detection
- Dependency-state correctness
- False-ready rate
- Audit completeness
- Next-action determinism

## Implemented boundary
- Completion requires an owner, no blocking dependencies and all required evidence verified.
- Adding or verifying evidence invalidates a prior completion state.
- Evidence records retain a verifier label for traceability.

## Security and operational limitations
- `verified_by` is a caller-supplied identity string, not an authenticated principal or cryptographic signature.
- The audit list and case state are in-memory mutable objects, not a tamper-evident or durable audit log.
- There is no access-control layer, tenant isolation, retention policy or database transaction boundary.
- The prototype does not establish legal sufficiency or authenticity of institutional evidence.

## Falsification
- A case becomes READY with missing evidence.
- An unresolved blocker is ignored.
- Ownerless cases progress to READY.
- A previously completed case remains COMPLETE after a required evidence or dependency change.
