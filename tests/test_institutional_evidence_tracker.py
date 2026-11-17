import unittest

from institutional_evidence_tracker import Evidence, InstitutionalCase, Status


class InstitutionalTrackerTests(unittest.TestCase):
    def test_owner_required(self):
        case = InstitutionalCase("C")
        self.assertEqual(case.status(), Status.WAITING_OWNER)

    def test_dependency_blocks(self):
        case = InstitutionalCase("C", decision_owner="office", blocking_dependencies={"inspection"})
        self.assertEqual(case.status(), Status.BLOCKED)
        self.assertIn("inspection", case.next_action())

    def test_verified_evidence_makes_case_ready(self):
        case = InstitutionalCase("C", decision_owner="office", required_evidence_ids={"E1"})
        case.add_evidence(Evidence("E1", "record", "official"))
        self.assertEqual(case.status(), Status.WAITING_EVIDENCE)
        case.verify_evidence("E1", verifier="records-office")
        self.assertEqual(case.status(), Status.READY)

    def test_complete_state_requires_readiness(self):
        case = InstitutionalCase("C", decision_owner="office")
        case.mark_complete()
        self.assertEqual(case.status(), Status.COMPLETE)

    def test_completion_flag_cannot_bypass_missing_evidence(self):
        case = InstitutionalCase("C", decision_owner="office", required_evidence_ids={"E1"})
        case.complete = True
        self.assertEqual(case.status(), Status.WAITING_EVIDENCE)
        with self.assertRaises(ValueError):
            case.mark_complete()

    def test_new_dependency_invalidates_completion(self):
        case = InstitutionalCase("C", decision_owner="office")
        case.mark_complete()
        case.add_blocking_dependency("external-approval")
        self.assertEqual(case.status(), Status.BLOCKED)
        self.assertIn("dependency-added:external-approval", case.audit)

    def test_verification_records_verifier_identity(self):
        case = InstitutionalCase("C", decision_owner="office", required_evidence_ids={"E1"})
        case.add_evidence(Evidence("E1", "record", "official"))
        case.verify_evidence("E1", verifier="records-office")
        self.assertEqual(case.evidence["E1"].verified_by, "records-office")
        self.assertIn("evidence-verified:E1:by:records-office", case.audit)

    def test_duplicate_evidence_id_with_changed_content_is_rejected(self):
        case = InstitutionalCase("C", decision_owner="office")
        case.add_evidence(Evidence("E1", "record", "official"))
        with self.assertRaises(ValueError):
            case.add_evidence(Evidence("E1", "changed record", "official"))


if __name__ == "__main__":
    unittest.main()
