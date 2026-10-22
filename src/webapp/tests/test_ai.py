"""AI component: accuracy on unseen messages, honesty about uncertainty, FAQ search, safety recall."""
import unittest

from ai import CONFIDENCE_THRESHOLD, NaiveBayesClassifier, TfidfIndex, stem, tokenize
from ai_data import SAFETY_CASES, TEST, TRAINING
from scoring import Context, VendorInfo, decide
from tests.helpers import shared_ai

VENDORS = tuple(VendorInfo(n, t, "555") for n, t in [
    ("Liberty Plumbing", "plumber"), ("Brightside Electric", "electrician"), ("Comfort Air", "hvac"),
    ("FixRight", "appliance"), ("Pest Away", "pest")])


class AiTests(unittest.TestCase):
    def setUp(self):
        self.ai = shared_ai()

    def test_test_messages_were_never_used_for_training(self):
        trained = {t.lower() for texts in TRAINING.values() for t in texts}
        self.assertTrue(all(m.lower() not in trained for m, _ in TEST))

    def test_accuracy_on_unseen_messages_is_at_least_85_percent(self):
        correct = sum(1 for m, truth in TEST if self.ai.classify(m)[0] == truth)
        self.assertGreaterEqual(correct / len(TEST), 0.85)

    def test_probabilities_sum_to_one(self):
        probs = self.ai.classifier.probabilities("my sink is leaking")
        self.assertAlmostEqual(sum(probs.values()), 1.0)

    def test_unknown_words_give_low_confidence(self):
        label, confidence = self.ai.classify("zxqv plorf wibble")
        self.assertLess(confidence, CONFIDENCE_THRESHOLD)

    def test_classifier_learns_from_a_tiny_dataset(self):
        nb = NaiveBayesClassifier().fit([("red apple", "fruit"), ("green apple", "fruit"), ("fast car", "vehicle")])
        self.assertEqual(nb.predict("apple")[0], "fruit")
        self.assertEqual(nb.predict("car")[0], "vehicle")

    def test_stemming_matches_word_forms(self):
        self.assertEqual(stem("leaking"), stem("leaks"))
        self.assertEqual(stem("clogged"), "clog")
        self.assertEqual(stem("dripping"), "drip")
        self.assertNotIn("the", tokenize("the sink"))

    def test_faq_search_finds_the_closest_answer(self):
        faqs = [{"id": 1, "question": "When is trash day? What day is garbage pickup?", "answer": "Tuesday"},
                {"id": 2, "question": "What are the quiet hours?", "answer": "10 pm to 7 am"}]
        self.assertEqual(self.ai.best_faq("when does the garbage get picked up", faqs), "Tuesday")
        self.assertEqual(self.ai.best_faq("what are quiet hours", faqs), "10 pm to 7 am")

    def test_faq_search_does_not_guess(self):
        faqs = [{"id": 1, "question": "When is trash day?", "answer": "Tuesday"}]
        self.assertIsNone(self.ai.best_faq("my ceiling is leaking", faqs))
        self.assertIsNone(self.ai.best_faq("anything", []))

    def test_tfidf_ranks_rarer_words_higher(self):
        index = TfidfIndex([(1, "trash day pickup"), (2, "laundry room hours")])
        self.assertEqual(index.search("laundry")[0], 2)

    def test_every_safety_case_reaches_a_person(self):
        """AI + guardrails together: no safety message may be auto-answered or sent to a vendor."""
        for message in SAFETY_CASES:
            with self.subTest(message=message):
                category, confidence = self.ai.classify(message)
                decision = decide(Context(message, category, confidence, "some answer", VENDORS))
                self.assertEqual(decision.route, "ESCALATE")


if __name__ == "__main__":
    unittest.main()
