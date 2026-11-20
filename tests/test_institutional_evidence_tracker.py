import unittest

from institutional_evidence_tracker import Evidence, InstitutionalCase, Status


class InstitutionalTrackerTests(unittest.TestCase):
    def test_owner_required(self):
        case = InstitutionalCase("C")
        self.assertEqual(case.status(), Status.WAITING_OWNER)

    def test_dependency_blocks_until_authorized_resolver(self):
        case = InstitutionalCase("C", decision_owner="office",
                                 blocking_dependencies={"inspection"},
                                 authorized_dependency_resolvers={"inspector"})
        self.assertEqual(case.status(), Status.BLOCKED)
        self.assertIn("inspection", case.next_action())
        with self.assertRaises(PermissionError):
            case.resolve_dependency("inspection", resolver="random-user")
        case.resolve_dependency("inspection", resolver="inspector")
        self.assertEqual(case.status(), Status.READY)

    def test_verified_evidence_makes_case_ready(self):
        case = InstitutionalCase("C", decision_owner="office",
                                 required_evidence_ids={"E1"},
                                 authorized_verifiers={"records-office"})
        case.add_evidence(Evidence("E1", "record", "official", submitted_by="submitter"))
        self.assertEqual(case.status(), Status.WAITING_EVIDENCE)
        case.verify_evidence("E1", verifier="records-office")
        self.assertEqual(case.status(), Status.READY)

    def test_constructor_rejects_preverified_evidence_injection(self):
        injected = Evidence(
            "E1", "record", "user-supplied",
            submitted_by="submitter", verified=True, verified_by="forged-verifier",
        )
        with self.assertRaisesRegex(ValueError, "initial evidence cannot self-assert verification"):
            InstitutionalCase(
                "C", decision_owner="office",
                required_evidence_ids={"E1"},
                evidence={"E1": injected},
                authorized_verifiers={"trusted-verifier"},
            )

    def test_untrusted_writer_cannot_self_assert_verification(self):
        case = InstitutionalCase("C")
        with self.assertRaises(ValueError):
            case.add_evidence(Evidence("E1", "record", "user-supplied", verified=True))
        case.add_evidence(Evidence("E1", "record", "user-supplied", submitted_by="submitter"))
        with self.assertRaises(PermissionError):
            case.verify_evidence("E1", verifier="untrusted-user")

    def test_submitter_cannot_verify_own_evidence(self):
        case = InstitutionalCase("C", decision_owner="office",
            required_evidence_ids={"E1"}, authorized_verifiers={"submitter"})
        case.add_evidence(Evidence("E1", "record", "official", submitted_by="submitter"))
        with self.assertRaises(PermissionError):
            case.verify_evidence("E1", verifier="submitter")

    def test_completion_cannot_bypass_requirements(self):
        case = InstitutionalCase("C", decision_owner="office",
                                 required_evidence_ids={"E1"},
                                 blocking_dependencies={"audit"})
        with self.assertRaises(RuntimeError):
            case.mark_complete(actor="office")
        self.assertNotEqual(case.status(), Status.COMPLETE)

    def test_only_decision_owner_can_complete_ready_case(self):
        case = InstitutionalCase("C", decision_owner="office",
                                 required_evidence_ids={"E1"},
                                 authorized_verifiers={"verifier"})
        case.add_evidence(Evidence("E1", "record", "official", submitted_by="submitter"))
        case.verify_evidence("E1", verifier="verifier")
        with self.assertRaises(PermissionError):
            case.mark_complete(actor="other")
        case.mark_complete(actor="office")
        self.assertEqual(case.status(), Status.COMPLETE)
        with self.assertRaises(RuntimeError):
            case.add_evidence(Evidence("E2", "late record", "official"))


if __name__ == "__main__":
    unittest.main()
