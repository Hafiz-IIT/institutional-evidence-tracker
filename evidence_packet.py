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
            "verification": (
                {
                    "verifier_id": item.verification.verifier_id,
                    "method": item.verification.method,
                    "verified_at": item.verification.verified_at,
                }
                if item.verification is not None else None
            ),
        }
        for item in sorted(case.evidence.values(), key=lambda item: item.evidence_id)
    ]

    completion = None
    if case.completion_record is not None:
        completion = {
            "approved_by": case.completion_record.approved_by,
            "decision_reference": case.completion_record.decision_reference,
            "completed_at": case.completion_record.completed_at,
        }

    payload = {
        "case_id": case.case_id,
        "decision_owner": case.decision_owner,
        "required_evidence_ids": sorted(case.required_evidence_ids),
        "evidence": evidence,
        "blocking_dependencies": sorted(case.blocking_dependencies),
        "status": case.status().value,
        "next_action": case.next_action(),
        "completion": completion,
        "audit": list(case.audit),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return payload
