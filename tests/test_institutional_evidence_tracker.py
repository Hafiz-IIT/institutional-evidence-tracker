import unittest

from institutional_evidence_tracker import Evidence, InstitutionalCase, Status


class InstitutionalTrackerTests(unittest.TestCase):
    def setUp(self):
        self.case = InstitutionalCase("C", decision_owner="office", required_evidence_ids={"E1"})
        self.case.add_evidence(Evidence("E1", "record", "official"))

    def test_owner_required(self):
        case = InstitutionalCase("C")
        self.assertEqual(case.status(), Status.WAITING_OWNER)

    def test_dependency_blocks_and_unknown_resolution_rejected(self):
        case = InstitutionalCase("C", decision_owner="office")
        case.add_dependency("inspection")
        self.assertEqual(case.status(), Status.BLOCKED)
        self.assertIn("inspection", case.next_action())
        with self.assertRaises(KeyError):
            case.resolve_dependency("unknown")
        case.resolve_dependency("inspection")
        self.assertEqual(case.status(), Status.READY)

    def test_verified_evidence_requires_verifier_method_and_time(self):
        self.assertEqual(self.case.status(), Status.WAITING_EVIDENCE)
        self.case.verify_evidence(
            "E1",
            verifier_id="reviewer-1",
            method="official-register-cross-check",
            verified_at=100.0,
        )
        self.assertEqual(self.case.status(), Status.READY)
        record = self.case.evidence["E1"].verification
        self.assertEqual(record.verifier_id, "reviewer-1")
        self.assertEqual(record.method, "official-register-cross-check")
        self.assertEqual(record.verified_at, 100.0)

    def test_case_cannot_be_marked_complete_before_ready(self):
        with self.assertRaisesRegex(ValueError, "READY"):
            self.case.mark_complete(
                approved_by="office",
                decision_reference="DEC-1",
                completed_at=101,
            )

    def test_completion_requires_approval_and_is_invalidated_by_new_state(self):
        self.case.verify_evidence("E1", verifier_id="reviewer", method="cross-check", verified_at=100)
        self.case.mark_complete(approved_by="office", decision_reference="DEC-100", completed_at=101)
        self.assertEqual(self.case.status(), Status.COMPLETE)
        self.assertTrue(self.case.complete)
        self.case.add_dependency("new-inspection")
        self.assertEqual(self.case.status(), Status.BLOCKED)
        self.assertFalse(self.case.complete)
        self.assertIsNone(self.case.completion_record)

    def test_only_assigned_decision_owner_can_approve_completion(self):
        self.case.verify_evidence("E1", verifier_id="reviewer", method="register-check", verified_at=100)
        with self.assertRaisesRegex(ValueError, "decision_owner"):
            self.case.mark_complete(approved_by="different-person", decision_reference="DEC-1", completed_at=101)

    def test_complete_is_read_only(self):
        with self.assertRaises(AttributeError):
            self.case.complete = True

    def test_duplicate_evidence_ids_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate evidence_id"):
            self.case.add_evidence(Evidence("E1", "replacement", "unknown"))

    def test_verification_changes_state_and_audit(self):
        self.case.verify_evidence("E1", verifier_id="reviewer", method="cross-check", verified_at=100)
        self.assertTrue(self.case.evidence["E1"].verified)
        self.assertTrue(any(event.startswith("evidence-verified:E1") for event in self.case.audit))


    def test_completion_time_cannot_precede_evidence_verification(self):
        self.case.verify_evidence("E1", verifier_id="reviewer", method="register-check", verified_at=100)
        with self.assertRaisesRegex(ValueError, "cannot precede"):
            self.case.mark_complete(approved_by="office", decision_reference="DEC-1", completed_at=99)

    def test_completion_is_invalidated_when_requirements_or_owner_change(self):
        self.case.verify_evidence("E1", verifier_id="reviewer", method="register-check", verified_at=100)
        self.case.mark_complete(approved_by="office", decision_reference="DEC-1", completed_at=101)
        self.case.require_evidence("E2")
        self.assertEqual(self.case.status(), Status.WAITING_EVIDENCE)
        self.assertIsNone(self.case.completion_record)
        self.case.add_evidence(Evidence("E2", "second record", "official"))
        self.case.verify_evidence("E2", verifier_id="reviewer", method="register-check", verified_at=102)
        self.case.mark_complete(approved_by="office", decision_reference="DEC-2", completed_at=103)
        self.case.decision_owner = "new-owner"
        self.assertEqual(self.case.status(), Status.READY)
        self.assertIsNone(self.case.completion_record)

    def test_internal_collections_are_read_only(self):
        with self.assertRaises(AttributeError):
            self.case.required_evidence_ids.add("E2")
        with self.assertRaises(TypeError):
            self.case.evidence["E2"] = Evidence("E2", "record", "official")
        with self.assertRaises(AttributeError):
            self.case.blocking_dependencies.add("inspection")
        with self.assertRaises(AttributeError):
            self.case.audit.append("forged-event")

    def test_invalid_verification_record_is_rejected(self):
        for verifier, method, at in (("", "cross-check", 1), ("reviewer", "", 1), ("reviewer", "cross-check", float("nan"))):
            with self.subTest(verifier=verifier, method=method, at=at), self.assertRaises(ValueError):
                self.case.verify_evidence("E1", verifier_id=verifier, method=method, verified_at=at)


if __name__ == "__main__":
    unittest.main()
