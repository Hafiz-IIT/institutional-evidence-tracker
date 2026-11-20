# Architecture

Case → decision owner → required evidence IDs → provenance/verification state → blocking dependencies → WAITING_OWNER / BLOCKED / WAITING_EVIDENCE / READY / COMPLETE → next action + audit.

## Trust and completion invariants
- Evidence cannot self-assert verification; only configured verifiers can mark it verified.
- Dependencies can only be resolved by configured resolvers.
- Only the designated decision owner can complete a case, and only after required evidence is verified and blockers are cleared.
- Completed cases reject further mutation.

These are application-level role checks. The prototype does not authenticate identities or cryptographically validate evidence provenance.

## Invariants
1. A case without a decision owner cannot be READY.
2. Blocking dependencies take precedence over readiness.
3. Required evidence must exist and be verified before READY.
