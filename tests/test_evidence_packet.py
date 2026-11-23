import unittest

from evidence_packet import build_packet
from institutional_evidence_tracker import Evidence, InstitutionalCase


class EvidencePacketTests(unittest.TestCase):
    def test_packet_hash_is_deterministic(self):
        case = InstitutionalCase("C", decision_owner="office", required_evidence_ids={"E1"})
        case.add_evidence(Evidence("E1", "record", "official"))
        a = build_packet(case)
        b = build_packet(case)
        self.assertEqual(a["sha256"], b["sha256"])

    def test_verification_changes_packet_hash_and_records_verifier(self):
        case = InstitutionalCase("C", decision_owner="office", required_evidence_ids={"E1"})
        case.add_evidence(Evidence("E1", "record", "official"))
        before = build_packet(case)["sha256"]
        case.verify_evidence("E1", verifier_id="reviewer", method="register-check", verified_at=100)
        after_packet = build_packet(case)
        self.assertNotEqual(before, after_packet["sha256"])
        self.assertEqual(after_packet["evidence"][0]["verification"]["verifier_id"], "reviewer")

    def test_packet_contains_completion_approval(self):
        case = InstitutionalCase("C", decision_owner="office", required_evidence_ids={"E1"})
        case.add_evidence(Evidence("E1", "record", "official"))
        case.verify_evidence("E1", verifier_id="reviewer", method="register-check", verified_at=100)
        case.mark_complete(approved_by="office-head", decision_reference="DEC-1", completed_at=101)
        packet = build_packet(case)
        self.assertEqual(packet["status"], "COMPLETE")
        self.assertEqual(packet["completion"]["decision_reference"], "DEC-1")


if __name__ == "__main__":
    unittest.main()
