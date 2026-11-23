from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
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


@dataclass
class InstitutionalCase:
    case_id: str
    decision_owner: str | None = None
    required_evidence_ids: set[str] = field(default_factory=set)
    evidence: dict[str, Evidence] = field(default_factory=dict)
    blocking_dependencies: set[str] = field(default_factory=set)
    audit: list[str] = field(default_factory=list)
    completion_record: CompletionRecord | None = None

    def __post_init__(self):
        _require_text(self.case_id, "case_id")
        if self.decision_owner is not None:
            _require_text(self.decision_owner, "decision_owner")
        if any(not isinstance(value, str) or not value.strip() for value in self.required_evidence_ids):
            raise ValueError("required_evidence_ids must contain non-empty strings")
        if any(not isinstance(value, str) or not value.strip() for value in self.blocking_dependencies):
            raise ValueError("blocking_dependencies must contain non-empty strings")

    @property
    def complete(self) -> bool:
        return self.status() == Status.COMPLETE

    def add_evidence(self, item: Evidence) -> None:
        if not isinstance(item, Evidence):
            raise TypeError("item must be an Evidence instance")
        if item.evidence_id in self.evidence:
            raise ValueError(f"duplicate evidence_id: {item.evidence_id}")
        self.evidence[item.evidence_id] = item
        self._invalidate_completion("evidence-added")
        self.audit.append(f"evidence-added:{item.evidence_id}")

    def verify_evidence(
        self,
        evidence_id: str,
        *,
        verifier_id: str,
        method: str,
        verified_at: float,
    ) -> None:
        item = self.evidence[evidence_id]
        record = VerificationRecord(verifier_id, method, verified_at)
        self.evidence[evidence_id] = replace(item, verification=record)
        self._invalidate_completion("evidence-reverified")
        self.audit.append(f"evidence-verified:{evidence_id}:{verifier_id}:{method}")

    def add_dependency(self, dependency: str) -> None:
        _require_text(dependency, "dependency")
        if dependency in self.blocking_dependencies:
            raise ValueError(f"dependency already exists: {dependency}")
        self.blocking_dependencies.add(dependency)
        self._invalidate_completion("dependency-added")
        self.audit.append(f"dependency-added:{dependency}")

    def resolve_dependency(self, dependency: str) -> None:
        if dependency not in self.blocking_dependencies:
            raise KeyError(f"unknown blocking dependency: {dependency}")
        self.blocking_dependencies.remove(dependency)
        self._invalidate_completion("dependency-resolved")
        self.audit.append(f"dependency-resolved:{dependency}")

    def mark_complete(
        self,
        *,
        approved_by: str,
        decision_reference: str,
        completed_at: float,
    ) -> None:
        if self.status() != Status.READY:
            raise ValueError("case can be completed only when status is READY")
        self.completion_record = CompletionRecord(approved_by, decision_reference, completed_at)
        self.audit.append(f"case-completed:{approved_by}:{decision_reference}")

    def status(self) -> Status:
        if not self.decision_owner:
            return Status.WAITING_OWNER
        if self.blocking_dependencies:
            return Status.BLOCKED
        missing_or_unverified = [
            evidence_id
            for evidence_id in self.required_evidence_ids
            if evidence_id not in self.evidence or not self.evidence[evidence_id].verified
        ]
        if missing_or_unverified:
            return Status.WAITING_EVIDENCE
        if self.completion_record is not None:
            return Status.COMPLETE
        return Status.READY

    def next_action(self) -> str:
        state = self.status()
        if state == Status.WAITING_OWNER:
            return "identify decision owner"
        if state == Status.BLOCKED:
            return "resolve dependency: " + sorted(self.blocking_dependencies)[0]
        if state == Status.WAITING_EVIDENCE:
            missing = sorted(
                evidence_id
                for evidence_id in self.required_evidence_ids
                if evidence_id not in self.evidence or not self.evidence[evidence_id].verified
            )
            return "obtain/verify evidence: " + missing[0]
        if state == Status.READY:
            return "submit evidence packet to decision owner"
        return "case complete"

    def _invalidate_completion(self, reason: str) -> None:
        if self.completion_record is not None:
            self.completion_record = None
            self.audit.append(f"completion-invalidated:{reason}")


if __name__ == "__main__":
    case = InstitutionalCase("C1", decision_owner="records-office", required_evidence_ids={"E1"})
    case.add_evidence(Evidence("E1", "certified record", "official-copy"))
    case.verify_evidence("E1", verifier_id="records-reviewer", method="source-register-cross-check", verified_at=100)
    print(case.status(), case.next_action())
