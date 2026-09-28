from __future__ import annotations

import hashlib
import json

from institutional_evidence_tracker import InstitutionalCase


def build_packet(case: InstitutionalCase) -> dict:
    evidence = [
        {
            "evidence_id": item.evidence_id,
            "description": item.description,
            "provenance": item.provenance,
            "verified": item.verified,
        }
        for item in sorted(case.evidence.values(), key=lambda item: item.evidence_id)
    ]

    payload = {
        "case_id": case.case_id,
        "decision_owner": case.decision_owner,
        "required_evidence_ids": sorted(case.required_evidence_ids),
        "evidence": evidence,
        "blocking_dependencies": sorted(case.blocking_dependencies),
        "status": case.status().value,
        "next_action": case.next_action(),
        "audit": list(case.audit),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return payload
