from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Status(str, Enum):
    WAITING_EVIDENCE = "WAITING_EVIDENCE"
    WAITING_OWNER = "WAITING_OWNER"
    BLOCKED = "BLOCKED"
    READY = "READY"
    COMPLETE = "COMPLETE"


@dataclass
class Evidence:
    evidence_id: str
    description: str
    provenance: str
    verified: bool = False


@dataclass
class InstitutionalCase:
    case_id: str
    decision_owner: str | None = None
    required_evidence_ids: set[str] = field(default_factory=set)
    evidence: dict[str, Evidence] = field(default_factory=dict)
    blocking_dependencies: set[str] = field(default_factory=set)
    complete: bool = False
    audit: list[str] = field(default_factory=list)

    def add_evidence(self, item: Evidence) -> None:
        self.evidence[item.evidence_id] = item
        self.audit.append(f"evidence-added:{item.evidence_id}")

    def verify_evidence(self, evidence_id: str) -> None:
        item = self.evidence[evidence_id]
        self.evidence[evidence_id] = Evidence(
            item.evidence_id, item.description, item.provenance, True
        )
        self.audit.append(f"evidence-verified:{evidence_id}")

    def resolve_dependency(self, dependency: str) -> None:
        self.blocking_dependencies.discard(dependency)
        self.audit.append(f"dependency-resolved:{dependency}")

    def status(self) -> Status:
        if self.complete:
            return Status.COMPLETE
        if not self.decision_owner:
            return Status.WAITING_OWNER
        if self.blocking_dependencies:
            return Status.BLOCKED
        missing_or_unverified = [
            eid
            for eid in self.required_evidence_ids
            if eid not in self.evidence or not self.evidence[eid].verified
        ]
        if missing_or_unverified:
            return Status.WAITING_EVIDENCE
        return Status.READY

    def next_action(self) -> str:
        state = self.status()
        if state == Status.WAITING_OWNER:
            return "identify decision owner"
        if state == Status.BLOCKED:
            return "resolve dependency: " + sorted(self.blocking_dependencies)[0]
        if state == Status.WAITING_EVIDENCE:
            missing = sorted(
                eid for eid in self.required_evidence_ids
                if eid not in self.evidence or not self.evidence[eid].verified
            )
            return "obtain/verify evidence: " + missing[0]
        if state == Status.READY:
            return "submit evidence packet to decision owner"
        return "case complete"


if __name__ == "__main__":
    case = InstitutionalCase("C1", decision_owner="records-office", required_evidence_ids={"E1"})
    case.add_evidence(Evidence("E1", "certified record", "official-copy"))
    print(case.status(), case.next_action())
