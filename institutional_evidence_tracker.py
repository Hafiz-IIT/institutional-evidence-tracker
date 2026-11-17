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
    verified_by: str | None = None


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
        if not item.evidence_id or not item.description or not item.provenance:
            raise ValueError("evidence id, description and provenance are required")
        existing = self.evidence.get(item.evidence_id)
        if existing is not None and existing != item:
            raise ValueError("evidence id already exists with different content")
        self.evidence[item.evidence_id] = item
        self.complete = False
        self.audit.append(f"evidence-added:{item.evidence_id}")

    def verify_evidence(self, evidence_id: str, *, verifier: str) -> None:
        if not isinstance(verifier, str) or not verifier.strip():
            raise ValueError("verifier identity is required")
        item = self.evidence[evidence_id]
        self.evidence[evidence_id] = Evidence(
            item.evidence_id, item.description, item.provenance, True, verifier.strip()
        )
        self.complete = False
        self.audit.append(f"evidence-verified:{evidence_id}:by:{verifier.strip()}")

    def add_blocking_dependency(self, dependency: str) -> None:
        if not isinstance(dependency, str) or not dependency.strip():
            raise ValueError("dependency must be a non-empty string")
        self.blocking_dependencies.add(dependency)
        self.complete = False
        self.audit.append(f"dependency-added:{dependency}")

    def resolve_dependency(self, dependency: str) -> None:
        self.blocking_dependencies.discard(dependency)
        self.audit.append(f"dependency-resolved:{dependency}")

    def _readiness(self) -> Status:
        if not self.decision_owner:
            return Status.WAITING_OWNER
        if self.blocking_dependencies:
            return Status.BLOCKED
        missing_or_unverified = [
            eid for eid in self.required_evidence_ids
            if eid not in self.evidence or not self.evidence[eid].verified
        ]
        return Status.WAITING_EVIDENCE if missing_or_unverified else Status.READY

    def status(self) -> Status:
        readiness = self._readiness()
        if self.complete and readiness == Status.READY:
            return Status.COMPLETE
        return readiness

    def mark_complete(self) -> None:
        readiness = self._readiness()
        if readiness != Status.READY:
            raise ValueError(f"case cannot be completed while status is {readiness.value}")
        self.complete = True
        self.audit.append("case-completed")

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
