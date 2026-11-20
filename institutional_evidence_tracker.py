from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Mapping

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
    submitted_by: str | None = None
    verified: bool = False
    verified_by: str | None = None

    def __post_init__(self):
        for name, value in (("evidence_id", self.evidence_id), ("description", self.description),
                            ("provenance", self.provenance)):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.submitted_by is not None and (not isinstance(self.submitted_by, str) or not self.submitted_by.strip()):
            raise ValueError("submitted_by must be non-empty when supplied")
        if not isinstance(self.verified, bool):
            raise ValueError("verified must be boolean")
        if self.verified and (not isinstance(self.verified_by, str) or not self.verified_by.strip()):
            raise ValueError("verified evidence requires verifier attribution")
        if not self.verified and self.verified_by is not None:
            raise ValueError("unverified evidence cannot have verifier attribution")

@dataclass
class InstitutionalCase:
    case_id: str
    decision_owner: str | None = None
    required_evidence_ids: set[str] = field(default_factory=set)
    evidence: Mapping[str, Evidence] = field(default_factory=dict)
    blocking_dependencies: set[str] = field(default_factory=set)
    authorized_verifiers: set[str] = field(default_factory=set)
    authorized_dependency_resolvers: set[str] = field(default_factory=set)
    _complete: bool = field(default=False, init=False, repr=False)
    audit: list[str] = field(default_factory=list)
    _evidence: dict[str, Evidence] = field(default_factory=dict, init=False, repr=False)
    _blocking_dependencies: set[str] = field(default_factory=set, init=False, repr=False)
    _audit: list[str] = field(default_factory=list, init=False, repr=False)
    _initialized: bool = field(default=False, init=False, repr=False)

    def __setattr__(self, name, value):
        if getattr(self, "_initialized", False) and name in {
            "case_id", "decision_owner", "required_evidence_ids", "evidence",
            "blocking_dependencies", "authorized_verifiers",
            "authorized_dependency_resolvers", "audit",
        }:
            raise AttributeError("case state is managed through its public methods")
        if getattr(self, "_complete", False):
            raise AttributeError("completed cases are immutable")
        object.__setattr__(self, name, value)

    def __post_init__(self):
        self._required_text("case_id", self.case_id)
        if self.decision_owner is not None:
            self._required_text("decision_owner", self.decision_owner)
        for name, values in (("required_evidence_ids", self.required_evidence_ids),
                             ("blocking_dependencies", self.blocking_dependencies),
                             ("authorized_verifiers", self.authorized_verifiers),
                             ("authorized_dependency_resolvers", self.authorized_dependency_resolvers)):
            if not isinstance(values, set) or any(not isinstance(v, str) or not v.strip() for v in values):
                raise ValueError(f"{name} must be a set of non-empty strings")
        if not isinstance(self.evidence, dict) and not hasattr(self.evidence, "items"):
            raise ValueError("evidence must map evidence IDs to Evidence records")
        initial_evidence = dict(self.evidence)
        if any(not isinstance(item, Evidence) or key != item.evidence_id for key, item in initial_evidence.items()):
            raise ValueError("evidence must map evidence IDs to Evidence records")
        if any(item.verified or item.verified_by is not None for item in initial_evidence.values()):
            raise ValueError("initial evidence cannot self-assert verification; use verify_evidence() with an authorized verifier")
        # Detach caller-owned containers, expose read-only snapshots, and keep
        # mutation behind the case methods that enforce the authorization rules.
        self._evidence = initial_evidence
        self.evidence = MappingProxyType(self._evidence)
        self.required_evidence_ids = frozenset(self.required_evidence_ids)
        self._blocking_dependencies = set(self.blocking_dependencies)
        self.blocking_dependencies = frozenset(self._blocking_dependencies)
        self.authorized_verifiers = frozenset(self.authorized_verifiers)
        self.authorized_dependency_resolvers = frozenset(self.authorized_dependency_resolvers)
        self._audit = list(self.audit)
        self.audit = tuple(self._audit)
        self._initialized = True

    @property
    def complete(self) -> bool:
        return self._complete

    @staticmethod
    def _required_text(name: str, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a non-empty string")

    def _ensure_open(self) -> None:
        if self._complete:
            raise RuntimeError("completed cases are immutable")

    def add_evidence(self, item: Evidence) -> None:
        self._ensure_open()
        if not isinstance(item, Evidence):
            raise TypeError("item must be an Evidence record")
        self._required_text("submitted_by", item.submitted_by)
        if item.evidence_id in self._evidence:
            raise ValueError("duplicate evidence_id")
        if item.verified or item.verified_by is not None:
            raise ValueError("evidence cannot self-assert verification")
        self._evidence[item.evidence_id] = item
        self._audit.append(f"evidence-added:{item.evidence_id}:by:{item.submitted_by}")

    def verify_evidence(self, evidence_id: str, *, verifier: str) -> None:
        self._ensure_open()
        self._required_text("evidence_id", evidence_id)
        self._required_text("verifier", verifier)
        if verifier not in self.authorized_verifiers:
            raise PermissionError(f"{verifier} is not an authorized evidence verifier")
        if evidence_id not in self.evidence:
            raise KeyError(evidence_id)
        item = self._evidence[evidence_id]
        if item.submitted_by == verifier:
            raise PermissionError("evidence submitter cannot verify their own submission")
        if item.verified:
            raise ValueError("evidence is already verified")
        self._evidence[evidence_id] = Evidence(
            item.evidence_id, item.description, item.provenance,
            submitted_by=item.submitted_by, verified=True, verified_by=verifier,
        )
        self._audit.append(f"evidence-verified:{evidence_id}:by:{verifier}")

    def add_blocking_dependency(self, dependency: str) -> None:
        self._ensure_open()
        self._required_text("dependency", dependency)
        if dependency in self._blocking_dependencies:
            raise ValueError("duplicate blocking dependency")
        self._blocking_dependencies.add(dependency)
        self.audit.append(f"dependency-added:{dependency}")

    def resolve_dependency(self, dependency: str, *, resolver: str) -> None:
        self._ensure_open()
        self._required_text("dependency", dependency)
        self._required_text("resolver", resolver)
        if resolver not in self.authorized_dependency_resolvers:
            raise PermissionError(f"{resolver} is not an authorized dependency resolver")
        if dependency not in self._blocking_dependencies:
            raise KeyError(dependency)
        self._blocking_dependencies.remove(dependency)
        self.audit.append(f"dependency-resolved:{dependency}:{resolver}")

    def status(self) -> Status:
        if self._complete: return Status.COMPLETE
        if not self.decision_owner: return Status.WAITING_OWNER
        if self._blocking_dependencies: return Status.BLOCKED
        missing = [eid for eid in self.required_evidence_ids
                   if eid not in self._evidence or not self._evidence[eid].verified]
        return Status.WAITING_EVIDENCE if missing else Status.READY

    def mark_complete(self, *, actor: str) -> None:
        self._ensure_open()
        self._required_text("actor", actor)
        if actor != self.decision_owner:
            raise PermissionError("only the designated decision owner may complete the case")
        if self.status() != Status.READY:
            raise RuntimeError("case cannot complete until owner, dependencies, and required evidence are ready")
        self._complete = True
        self._audit.append(f"case-completed:{actor}")

    def next_action(self) -> str:
        state = self.status()
        if state == Status.WAITING_OWNER: return "identify decision owner"
        if state == Status.BLOCKED: return "resolve dependency: " + sorted(self._blocking_dependencies)[0]
        if state == Status.WAITING_EVIDENCE:
            missing = sorted(eid for eid in self.required_evidence_ids
                             if eid not in self._evidence or not self._evidence[eid].verified)
            return "obtain/verify evidence: " + missing[0]
        if state == Status.READY: return "submit evidence packet to decision owner"
        return "case complete"

if __name__ == "__main__":
    case = InstitutionalCase("C1", decision_owner="records-office",
        required_evidence_ids={"E1"}, authorized_verifiers={"records-verifier"})
    case.add_evidence(Evidence("E1", "certified record", "official-copy", submitted_by="trader"))
    case.verify_evidence("E1", verifier="records-verifier")
    print(case.status(), case.next_action())
