from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from types import MappingProxyType
import math


class Status(str, Enum):
    WAITING_EVIDENCE = "WAITING_EVIDENCE"
    WAITING_OWNER = "WAITING_OWNER"
    BLOCKED = "BLOCKED"
    READY = "READY"
    COMPLETE = "COMPLETE"


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_finite_time(value: float, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{field_name} must be a finite number")


@dataclass(frozen=True)
class VerificationRecord:
    verifier_id: str
    method: str
    verified_at: float

    def __post_init__(self):
        _require_text(self.verifier_id, "verifier_id")
        _require_text(self.method, "method")
        _require_finite_time(self.verified_at, "verified_at")


@dataclass(frozen=True)
class CompletionRecord:
    approved_by: str
    decision_reference: str
    completed_at: float

    def __post_init__(self):
        _require_text(self.approved_by, "approved_by")
        _require_text(self.decision_reference, "decision_reference")
        _require_finite_time(self.completed_at, "completed_at")


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    description: str
    provenance: str
    verification: VerificationRecord | None = None

    def __post_init__(self):
        _require_text(self.evidence_id, "evidence_id")
        _require_text(self.description, "description")
        _require_text(self.provenance, "provenance")

    @property
    def verified(self) -> bool:
        return self.verification is not None


class InstitutionalCase:
    """Mutable workflow aggregate with read-only views of its internal collections.

    Verifier IDs, methods and approver IDs are recorded claims supplied by the
    calling application. This class does not authenticate those identities.
    """

    def __init__(
        self,
        case_id: str,
        decision_owner: str | None = None,
        required_evidence_ids=None,
        blocking_dependencies=None,
    ):
        _require_text(case_id, "case_id")
        if decision_owner is not None:
            _require_text(decision_owner, "decision_owner")
        required = set(required_evidence_ids or ())
        dependencies = set(blocking_dependencies or ())
        if any(not isinstance(value, str) or not value.strip() for value in required):
            raise ValueError("required_evidence_ids must contain non-empty strings")
        if any(not isinstance(value, str) or not value.strip() for value in dependencies):
            raise ValueError("blocking_dependencies must contain non-empty strings")
        self._case_id = case_id
        self._decision_owner = decision_owner
        self._required_evidence_ids = required
        self._evidence: dict[str, Evidence] = {}
        self._blocking_dependencies = dependencies
        self._audit: list[str] = []
        self._completion_record: CompletionRecord | None = None

    @property
    def case_id(self) -> str:
        return self._case_id

    @property
    def decision_owner(self) -> str | None:
        return self._decision_owner

    @decision_owner.setter
    def decision_owner(self, value: str | None) -> None:
        if value is not None:
            _require_text(value, "decision_owner")
        if value != self._decision_owner:
            self._decision_owner = value
            self._invalidate_completion("decision-owner-changed")
            self._audit.append("decision-owner-updated")

    @property
    def required_evidence_ids(self) -> frozenset[str]:
        return frozenset(self._required_evidence_ids)

    @property
    def evidence(self):
        return MappingProxyType(self._evidence)

    @property
    def blocking_dependencies(self) -> frozenset[str]:
        return frozenset(self._blocking_dependencies)

    @property
    def audit(self) -> tuple[str, ...]:
        return tuple(self._audit)

    @property
    def completion_record(self) -> CompletionRecord | None:
        return self._completion_record

    @property
    def complete(self) -> bool:
        return self.status() == Status.COMPLETE

    def require_evidence(self, evidence_id: str) -> None:
        _require_text(evidence_id, "evidence_id")
        if evidence_id not in self._required_evidence_ids:
            self._required_evidence_ids.add(evidence_id)
            self._invalidate_completion("required-evidence-changed")
            self._audit.append(f"evidence-required:{evidence_id}")

    def add_evidence(self, item: Evidence) -> None:
        if not isinstance(item, Evidence):
            raise TypeError("item must be an Evidence instance")
        if item.evidence_id in self._evidence:
            raise ValueError(f"duplicate evidence_id: {item.evidence_id}")
        self._evidence[item.evidence_id] = item
        self._invalidate_completion("evidence-added")
        self._audit.append(f"evidence-added:{item.evidence_id}")

    def verify_evidence(
        self,
        evidence_id: str,
        *,
        verifier_id: str,
        method: str,
        verified_at: float,
    ) -> None:
        item = self._evidence[evidence_id]
        record = VerificationRecord(verifier_id, method, verified_at)
        self._evidence[evidence_id] = replace(item, verification=record)
        self._invalidate_completion("evidence-reverified")
        self._audit.append(f"evidence-verified:{evidence_id}:{verifier_id}:{method}")

    def add_dependency(self, dependency: str) -> None:
        _require_text(dependency, "dependency")
        if dependency in self._blocking_dependencies:
            raise ValueError(f"dependency already exists: {dependency}")
        self._blocking_dependencies.add(dependency)
        self._invalidate_completion("dependency-added")
        self._audit.append(f"dependency-added:{dependency}")

    def resolve_dependency(self, dependency: str) -> None:
        if dependency not in self._blocking_dependencies:
            raise KeyError(f"unknown blocking dependency: {dependency}")
        self._blocking_dependencies.remove(dependency)
        self._invalidate_completion("dependency-resolved")
        self._audit.append(f"dependency-resolved:{dependency}")

    def mark_complete(
        self,
        *,
        approved_by: str,
        decision_reference: str,
        completed_at: float,
    ) -> None:
        if self.status() != Status.READY:
            raise ValueError("case can be completed only when status is READY")
        if approved_by != self._decision_owner:
            raise ValueError("approved_by must match the assigned decision_owner")
        record = CompletionRecord(approved_by, decision_reference, completed_at)
        required_times = [
            self._evidence[evidence_id].verification.verified_at
            for evidence_id in self._required_evidence_ids
        ]
        if any(verified_at > record.completed_at for verified_at in required_times):
            raise ValueError("completion time cannot precede required evidence verification")
        self._completion_record = record
        self._audit.append(f"case-completed:{approved_by}:{decision_reference}")

    def status(self) -> Status:
        if not self._decision_owner:
            return Status.WAITING_OWNER
        if self._blocking_dependencies:
            return Status.BLOCKED
        missing_or_unverified = [
            evidence_id
            for evidence_id in self._required_evidence_ids
            if evidence_id not in self._evidence or not self._evidence[evidence_id].verified
        ]
        if missing_or_unverified:
            return Status.WAITING_EVIDENCE
        if self._completion_record is not None:
            return Status.COMPLETE
        return Status.READY

    def next_action(self) -> str:
        state = self.status()
        if state == Status.WAITING_OWNER:
            return "identify decision owner"
        if state == Status.BLOCKED:
            return "resolve dependency: " + sorted(self._blocking_dependencies)[0]
        if state == Status.WAITING_EVIDENCE:
            missing = sorted(
                evidence_id
                for evidence_id in self._required_evidence_ids
                if evidence_id not in self._evidence or not self._evidence[evidence_id].verified
            )
            return "obtain/verify evidence: " + missing[0]
        if state == Status.READY:
            return "submit evidence packet to decision owner"
        return "case complete"

    def _invalidate_completion(self, reason: str) -> None:
        if self._completion_record is not None:
            self._completion_record = None
            self._audit.append(f"completion-invalidated:{reason}")


if __name__ == "__main__":
    case = InstitutionalCase("C1", decision_owner="records-office", required_evidence_ids={"E1"})
    case.add_evidence(Evidence("E1", "certified record", "official-copy"))
    case.verify_evidence("E1", verifier_id="records-reviewer", method="source-register-cross-check", verified_at=100)
    print(case.status(), case.next_action())
