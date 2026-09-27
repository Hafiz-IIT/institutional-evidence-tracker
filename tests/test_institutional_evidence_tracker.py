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
        case.verify_evidence("E1")
        self.assertEqual(case.status(), Status.READY)

    def test_complete_state(self):
        case = InstitutionalCase("C", decision_owner="office")
        case.complete = True
        self.assertEqual(case.status(), Status.COMPLETE)


if __name__ == "__main__":
    unittest.main()
