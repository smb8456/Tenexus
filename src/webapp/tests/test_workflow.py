"""IMPERATIVE layer: the ten ordered steps, validation, alerts, review."""
import unittest

from models import DomainError, PermissionDenied
from workflow import NotFound, ValidationError, process_request, review_request
from tests.helpers import fresh_repo, shared_ai

# (message, expected route). Same flavour of requests as the four prototypes.
NINE = [
    ("I smell gas in the kitchen", "ESCALATE"),
    ("I am locked out of my apartment", "ESCALATE"),
    ("There is smoke coming from the outlet", "ESCALATE"),
    ("Water is coming through the ceiling", "VENDOR"),     # the AI recognises it; keyword rules did not
    ("My sink is leaking", "VENDOR"),
    ("The toilet is clogged", "VENDOR"),
    ("The light switch in the hall is broken", "VENDOR"),
    ("When is trash day?", "ANSWER"),
    ("What are the quiet hours?", "ANSWER"),
]


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.repo = fresh_repo(self)
        self.ai = shared_ai()

    def run_one(self, message, tenant_id=1):
        return process_request(self.repo, self.ai, tenant_id, message)

    def count_requests(self):
        with self.repo.connect() as db:
            return db.execute("SELECT COUNT(*) FROM requests").fetchone()[0]

    def test_ten_steps_run_in_order(self):
        result = self.run_one("My sink is leaking under the cabinet")
        self.assertEqual([a["step"] for a in result["audit"]], list(range(1, 11)))
        self.assertEqual(result["audit"][0]["name"], "Receive request")
        self.assertEqual(result["audit"][6]["name"], "Decide route")
        self.assertEqual(result["audit"][8]["name"], "Save request")

    def test_audit_trail_is_saved_with_the_request(self):
        result = self.run_one("My sink is leaking under the cabinet")
        self.assertEqual(len(self.repo.audit_for(result["id"])), 10)

    def test_nine_scenarios_route_as_expected(self):
        for message, expected in NINE:
            with self.subTest(message=message):
                self.assertEqual(self.run_one(message)["route"], expected)

    def test_nine_scenarios_split_3_vendor_4_and_2(self):
        routes = [self.run_one(m)["route"] for m, _ in NINE]
        self.assertEqual((routes.count("ESCALATE"), routes.count("VENDOR"), routes.count("ANSWER")), (3, 4, 2))

    def test_escalation_queues_a_landlord_alert(self):
        result = self.run_one("I smell gas in the kitchen")
        self.assertIn("landlord alert queued for Ana Rivera", result["audit"][9]["detail"])
        self.assertEqual(result["status"], "ESCALATED")

    def test_gas_gets_emergency_guidance(self):
        self.assertIn("911", self.run_one("I smell gas in the kitchen")["tenant_message"])

    def test_vendor_referral_names_the_landlords_vendor(self):
        result = self.run_one("My sink is leaking under the cabinet")
        self.assertEqual((result["vendor_name"], result["vendor_phone"]), ("Liberty Plumbing", "555-0101"))
        self.assertIn("Liberty Plumbing", result["tenant_message"])

    def test_faq_answer_comes_from_the_tenants_own_property(self):
        self.assertIn("Tuesday", self.run_one("When is trash day?", tenant_id=1)["answer"])
        self.assertIn("Friday", self.run_one("When is trash day?", tenant_id=3)["answer"])

    def test_no_vendor_on_file_escalates(self):
        # Dev (tenant 3) lives at a property whose landlord has no electrician.
        result = self.run_one("The light switch in the hall is broken", tenant_id=3)
        self.assertEqual(result["route"], "ESCALATE")

    def test_bad_input_is_rejected_and_nothing_is_saved(self):
        for bad in (None, "", "   ", "hi", "x" * 1001, 42):
            with self.subTest(message=bad):
                with self.assertRaises(ValidationError):
                    self.run_one(bad)
        with self.assertRaises(ValidationError):
            process_request(self.repo, self.ai, "1", "My sink is leaking")
        with self.assertRaises(ValidationError):
            process_request(self.repo, self.ai, True, "My sink is leaking")
        self.assertEqual(self.count_requests(), 0)

    def test_unknown_tenant_is_not_found(self):
        with self.assertRaises(NotFound):
            self.run_one("My sink is leaking", tenant_id=999)

    def test_landlord_can_approve_and_agreement_is_tracked(self):
        result = self.run_one("My sink is leaking under the cabinet")
        review_request(self.repo, result["id"], 1, "VENDOR")
        self.assertEqual(self.repo.agreement(1)["agreement_pct"], 100.0)
        self.assertEqual(self.repo.get_request(result["id"])["status"], "REVIEWED")

    def test_landlord_correction_lowers_agreement(self):
        first = self.run_one("My sink is leaking under the cabinet")
        second = self.run_one("The toilet is clogged and will not flush")
        review_request(self.repo, first["id"], 1, "VENDOR")
        review_request(self.repo, second["id"], 1, "ESCALATE")
        self.assertEqual(self.repo.agreement(1)["agreement_pct"], 50.0)

    def test_the_wrong_landlord_cannot_review(self):
        result = self.run_one("My sink is leaking under the cabinet")
        with self.assertRaises(PermissionDenied):
            review_request(self.repo, result["id"], 2, "VENDOR")

    def test_review_of_missing_things_is_not_found(self):
        result = self.run_one("My sink is leaking under the cabinet")
        with self.assertRaises(NotFound):
            review_request(self.repo, 999, 1, "VENDOR")
        with self.assertRaises(NotFound):
            review_request(self.repo, result["id"], 999, "VENDOR")

    def test_reviewing_twice_is_rejected(self):
        result = self.run_one("My sink is leaking under the cabinet")
        review_request(self.repo, result["id"], 1, "VENDOR")
        with self.assertRaises(DomainError):
            review_request(self.repo, result["id"], 1, "VENDOR")


if __name__ == "__main__":
    unittest.main()
