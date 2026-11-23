# Status

## Implemented
- evidence objects with provenance metadata
- explicit verification records (verifier ID, method and timestamp)
- read-only external views of evidence, required evidence, dependencies and audit events
- decision-owner tracking
- required-evidence tracking
- blocking dependency tracking and explicit resolution
- READY/COMPLETE distinction
- completion requires the assigned decision owner, decision reference and timestamp
- completion is invalidated when relevant case state changes
- completion time cannot precede required evidence verification
- deterministic evidence packet with verification and completion records
- unit tests + GitHub Actions CI

## Security and governance boundary
Verifier IDs and approver IDs are recorded claims supplied by the calling application. This prototype does not authenticate those identities, verify source authenticity, protect the audit log against privileged tampering, or implement an institutional authorization service.

## Not claimed
- legal advice
- government integration
- real case records
- automatic legal conclusions
- institutional adoption
- regulatory compliance
- tamper-proof audit logging or authenticated sign-off

## Boundary
Generic administrative workflow software only. It is not legal advice, a case-management system used by any institution, or evidence that any real authority follows these states.
