# Architecture

Case → decision owner → required evidence IDs → provenance/verification state → blocking dependencies → WAITING_OWNER / BLOCKED / WAITING_EVIDENCE / READY / COMPLETE → next action + audit.

## Invariants
1. A case without a decision owner cannot be READY.
2. Blocking dependencies take precedence over readiness.
3. Required evidence must exist and be verified before READY.
