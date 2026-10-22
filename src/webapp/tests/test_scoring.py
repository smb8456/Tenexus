"""FUNCTIONAL layer: pure routing rules and safety guardrails."""
import dataclasses
import unittest

from scoring import (BASE_URGENCY, CONFIDENCE_THRESHOLD, Context, Decision, VendorInfo,
                     decide, route_counts, urgency_for)

VENDORS = (VendorInfo("Liberty Plumbing", "plumber", "555-0101"),
           VendorInfo("Brightside Electric", "electrician", "555-0102"))


def ctx(message="my sink is leaking", category="plumbing", confidence=0.9, faq=None, vendors=VENDORS):
    return Context(message, category, confidence, faq, vendors)


class ScoringTests(unittest.TestCase):
    # ---- guardrails ----
    def test_safety_keyword_always_escalates_even_if_ai_is_confident_and_wrong(self):
        d = decide(ctx("I smell gas near the sink", "plumbing", 0.99))
        self.assertEqual((d.route, d.urgency, d.guardrail), ("ESCALATE", 10, True))

    def test_sparks_mislabeled_as_electrical_still_escalates(self):
        d = decide(ctx("sparks coming from the light switch", "electrical", 0.95))
        self.assertEqual(d.route, "ESCALATE")
        self.assertTrue(d.guardrail)

    def test_lockout_guardrail(self):
        d = decide(ctx("I am locked out", "lockout", 0.9))
        self.assertEqual((d.route, d.urgency, d.guardrail), ("ESCALATE", 8, True))

    # ---- thresholds ----
    def test_low_confidence_goes_to_a_person(self):
        d = decide(ctx(confidence=CONFIDENCE_THRESHOLD - 0.01))
        self.assertEqual(d.route, "ESCALATE")
        self.assertIn("confidence", d.reason)

    def test_confidence_exactly_at_threshold_is_allowed(self):
        self.assertEqual(decide(ctx(confidence=CONFIDENCE_THRESHOLD)).route, "VENDOR")

    def test_high_urgency_escalates_without_a_keyword(self):
        # heating (6) + urgent wording (2) = 8
        d = decide(ctx("it is freezing in here", "heating", 0.9))
        self.assertEqual((d.route, d.urgency), ("ESCALATE", 8))

    def test_urgency_never_goes_above_10(self):
        self.assertEqual(urgency_for(ctx("emergency flood", "safety", 0.9)), 10)
        self.assertTrue(all(urgency_for(ctx("emergency", c, 0.9)) <= 10 for c in BASE_URGENCY))

    # ---- answers and vendors ----
    def test_question_with_approved_faq_is_answered(self):
        d = decide(ctx("when is trash day", "question", 0.9, faq="Tuesday night."))
        self.assertEqual((d.route, d.answer, d.needs_review), ("ANSWER", "Tuesday night.", False))

    def test_question_without_approved_faq_is_not_answered(self):
        self.assertEqual(decide(ctx("can I paint the walls", "question", 0.9, faq=None)).route, "ESCALATE")

    def test_known_vendor_is_referred(self):
        d = decide(ctx())
        self.assertEqual((d.route, d.vendor_name, d.vendor_phone), ("VENDOR", "Liberty Plumbing", "555-0101"))

    def test_missing_vendor_escalates(self):
        self.assertEqual(decide(ctx("the heat is out", "heating", 0.9)).route, "ESCALATE")

    def test_noise_complaints_go_to_the_landlord(self):
        self.assertEqual(decide(ctx("loud music", "noise", 0.9)).route, "ESCALATE")

    # ---- purity and immutability ----
    def test_same_input_gives_same_output(self):
        c = ctx()
        self.assertEqual(decide(c), decide(c))

    def test_inputs_are_not_changed(self):
        vendors = list(VENDORS)
        c = Context("my sink is leaking", "plumbing", 0.9, None, tuple(vendors))
        before = dataclasses.asdict(c)
        decide(c)
        self.assertEqual(dataclasses.asdict(c), before)
        self.assertEqual(vendors, list(VENDORS))

    def test_decisions_and_context_are_immutable(self):
        d = decide(ctx())
        with self.assertRaises(dataclasses.FrozenInstanceError):
            d.route = "ANSWER"
        with self.assertRaises(dataclasses.FrozenInstanceError):
            ctx().message = "changed"
        with self.assertRaises(TypeError):
            BASE_URGENCY["safety"] = 0

    def test_route_counts_uses_reduce_without_mutating_input(self):
        decisions = [Decision("ESCALATE", 9, "a"), Decision("VENDOR", 5, "b"), Decision("ESCALATE", 8, "c")]
        snapshot = list(decisions)
        self.assertEqual(route_counts(decisions), {"ESCALATE": 2, "VENDOR": 1})
        self.assertEqual(decisions, snapshot)


if __name__ == "__main__":
    unittest.main()
