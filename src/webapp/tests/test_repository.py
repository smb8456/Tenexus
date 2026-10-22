"""DECLARATIVE layer: SQL constraints and views."""
import sqlite3
import unittest

from tests.helpers import fresh_repo, insert_request


class SqlTests(unittest.TestCase):
    def setUp(self):
        self.repo = fresh_repo(self)

    # ---- constraints ----
    def test_bad_route_is_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            insert_request(self.repo, route="MAYBE")

    def test_short_message_is_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            insert_request(self.repo, message="hi")

    def test_urgency_and_confidence_ranges_are_enforced(self):
        with self.assertRaises(sqlite3.IntegrityError):
            insert_request(self.repo, urgency=11)
        with self.assertRaises(sqlite3.IntegrityError):
            insert_request(self.repo, confidence=1.5)

    def test_foreign_keys_are_enforced(self):
        with self.assertRaises(sqlite3.IntegrityError):
            insert_request(self.repo, tenant_id=999)

    def test_reviewed_fields_must_be_filled_together(self):
        with self.assertRaises(sqlite3.IntegrityError):
            insert_request(self.repo, landlord_route="VENDOR")     # no reviewed_at

    # ---- queue view ----
    def test_queue_is_most_urgent_then_oldest(self):
        a = insert_request(self.repo, urgency=5, created_at="2026-01-01 10:00:00.000")
        b = insert_request(self.repo, urgency=9, created_at="2026-01-02 10:00:00.000", route="ESCALATE", status="ESCALATED")
        c = insert_request(self.repo, urgency=5, created_at="2026-01-01 09:00:00.000")
        self.assertEqual([r["id"] for r in self.repo.queue(1)], [b, c, a])

    def test_queue_hides_answers_and_reviewed_requests(self):
        keep = insert_request(self.repo)
        insert_request(self.repo, route="ANSWER", status="ANSWERED", urgency=1, category="question")
        insert_request(self.repo, status="REVIEWED", landlord_route="VENDOR", reviewed_at="2026-01-03 10:00:00.000")
        self.assertEqual([r["id"] for r in self.repo.queue(1)], [keep])

    def test_queue_only_shows_the_landlords_own_properties(self):
        insert_request(self.repo)                                           # landlord 1
        other = insert_request(self.repo, tenant_id=3, property_id=2)       # landlord 2
        self.assertEqual([r["id"] for r in self.repo.queue(2)], [other])

    # ---- stats and agreement views ----
    def test_stats_view_counts_per_route(self):
        insert_request(self.repo)
        insert_request(self.repo)
        insert_request(self.repo, route="ESCALATE", status="ESCALATED")
        self.assertEqual(self.repo.stats(1), {"ANSWER": 0, "VENDOR": 2, "ESCALATE": 1})
        self.assertEqual(self.repo.stats(2), {"ANSWER": 0, "VENDOR": 0, "ESCALATE": 0})

    def test_agreement_view_computes_percentage(self):
        done = dict(status="REVIEWED", reviewed_at="2026-01-03 10:00:00.000")
        insert_request(self.repo, landlord_route="VENDOR", **done)       # agreed
        insert_request(self.repo, landlord_route="VENDOR", **done)       # agreed
        insert_request(self.repo, landlord_route="ESCALATE", **done)     # corrected
        insert_request(self.repo)                                         # not reviewed: ignored
        agreement = self.repo.agreement(1)
        self.assertEqual((agreement["reviewed"], agreement["agreed"], agreement["agreement_pct"]), (3, 2, 66.7))

    def test_agreement_with_no_reviews_is_empty(self):
        self.assertEqual(self.repo.agreement(1)["reviewed"], 0)


if __name__ == "__main__":
    unittest.main()
