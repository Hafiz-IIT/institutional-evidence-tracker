from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Status(str, Enum):
    WAITING_EVIDENCE = "WAITING_EVIDENCE"
    WAITING_OWNER = "WAITING_OWNER"
    BLOCKED = "BLOCKED"
    READY = "READY"
    COMPLETE = "COMPLETE"


@dataclass(frozen=True)
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
    authorized_verifiers: set[str] = field(default_factory=set)
    authorized_dependency_resolvers: set[str] = field(default_factory=set)
    _complete: bool = field(default=False, init=False, repr=False)
    audit: list[str] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return self._complete

    def _ensure_open(self) -> None:
        if self._complete:
            raise RuntimeError("completed cases are immutable")

    @staticmethod
    def _required_text(name: str, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a non-empty string")

    def add_evidence(self, item: Evidence) -> None:
        self._ensure_open()
        self._required_text("evidence_id", item.evidence_id)
        self._required_text("description", item.description)
        self._required_text("provenance", item.provenance)
        if item.evidence_id in self.evidence:
            raise ValueError("duplicate evidence_id")
        if item.verified:
            raise ValueError("evidence cannot self-assert verification")
        self.evidence[item.evidence_id] = item
        self.audit.append(f"evidence-added:{item.evidence_id}")

    def verify_evidence(self, evidence_id: str, *, verifier: str) -> None:
        self._ensure_open()
        self._required_text("verifier", verifier)
        if verifier not in self.authorized_verifiers:
            raise PermissionError(f"{verifier} is not an authorized evidence verifier")
        if evidence_id not in self.evidence:
            raise KeyError(evidence_id)
        item = self.evidence[evidence_id]
        self.evidence[evidence_id] = Evidence(
            item.evidence_id, item.description, item.provenance, True
        )
        self.audit.append(f"evidence-verified:{evidence_id}:{verifier}")

    def resolve_dependency(self, dependency: str, *, resolver: str) -> None:
        self._ensure_open()
        self._required_text("dependency", dependency)
        self._required_text("resolver", resolver)
        if resolver not in self.authorized_dependency_resolvers:
            raise PermissionError(f"{resolver} is not an authorized dependency resolver")
        if dependency not in self.blocking_dependencies:
            raise KeyError(dependency)
        self.blocking_dependencies.remove(dependency)
        self.audit.append(f"dependency-resolved:{dependency}:{resolver}")

    def status(self) -> Status:
        if self._complete:
            return Status.COMPLETE
        if not self.decision_owner:
            return Status.WAITING_OWNER
        if self.blocking_dependencies:
            return Status.BLOCKED
        missing_or_unverified = [
            eid for eid in self.required_evidence_ids
            if eid not in self.evidence or not self.evidence[eid].verified
        ]
        if missing_or_unverified:
            return Status.WAITING_EVIDENCE
        return Status.READY

    def mark_complete(self, *, actor: str) -> None:
        self._ensure_open()
        self._required_text("actor", actor)
        if actor != self.decision_owner:
            raise PermissionError("only the designated decision owner may complete the case")
        if self.status() != Status.READY:
            raise RuntimeError("case cannot complete until owner, dependencies, and required evidence are ready")
        self._complete = True
        self.audit.append(f"case-completed:{actor}")

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
    case = InstitutionalCase(
        "C1", decision_owner="records-office",
        required_evidence_ids={"E1"},
        authorized_verifiers={"records-verifier"},
    )
    case.add_evidence(Evidence("E1", "certified record", "official-copy"))
    case.verify_evidence("E1", verifier="records-verifier")
    print(case.status(), case.next_action())
