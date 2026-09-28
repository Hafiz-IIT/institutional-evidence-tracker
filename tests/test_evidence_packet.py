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

    def test_verification_changes_packet_hash(self):
        case = InstitutionalCase("C", decision_owner="office", required_evidence_ids={"E1"})
        case.add_evidence(Evidence("E1", "record", "official"))
        before = build_packet(case)["sha256"]
        case.verify_evidence("E1")
        after = build_packet(case)["sha256"]
        self.assertNotEqual(before, after)


if __name__ == "__main__":
    unittest.main()
