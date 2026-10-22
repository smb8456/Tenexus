"""Measure the AI honestly: accuracy on unseen messages, and what happens to its mistakes.

Run:  python evaluate_ai.py
"""
from ai import AIEngine, CONFIDENCE_THRESHOLD
from ai_data import SAFETY_CASES, TEST
from scoring import Context, VendorInfo, decide

VENDORS = tuple(VendorInfo(n, t, "555") for n, t in [
    ("Liberty Plumbing", "plumber"), ("Brightside Electric", "electrician"), ("Comfort Air HVAC", "hvac"),
    ("FixRight Appliance", "appliance"), ("Pest Away", "pest")])


def pipeline_route(engine, message):
    """AI + routing rules, as the web app runs them (FAQ answer assumed available)."""
    category, confidence = engine.classify(message)
    return decide(Context(message, category, confidence, "an approved answer", VENDORS)), category, confidence


def main():
    engine = AIEngine.trained()
    wrong = []
    print("Held-out test messages (never used for training)\n")
    for message, truth in TEST:
        decision, label, conf = pipeline_route(engine, message)
        ok = label == truth
        print(f"{'ok  ' if ok else 'MISS'} true={truth:10} ai={label:10} conf={conf:.2f} -> {decision.route:8} {message}")
        if not ok:
            wrong.append((message, truth, label, conf, decision))
    correct = len(TEST) - len(wrong)
    print(f"\nAccuracy: {correct}/{len(TEST)} = {100 * correct / len(TEST):.0f}%")

    print(f"\nMistakes ({len(wrong)}) and where they went (confidence threshold {CONFIDENCE_THRESHOLD}):")
    for message, truth, label, conf, d in wrong:
        print(f"  {message!r}: AI said {label} ({conf:.2f}), true {truth} -> {d.route}"
              f"{' (' + d.vendor_name + ')' if d.vendor_name else ''}")
    auto_answered = sum(1 for *_, d in wrong if d.route == "ANSWER")
    held_for_person = sum(1 for *_, d in wrong if d.route == "ESCALATE")
    print(f"  mistakes auto-answered to a tenant: {auto_answered}")
    print(f"  mistakes escalated to the landlord before reaching the tenant: {held_for_person}")
    print(f"  mistakes shown to the tenant as a vendor referral (landlord can correct afterwards): "
          f"{sum(1 for *_, d in wrong if d.route == 'VENDOR')}")

    safe = sum(1 for m in SAFETY_CASES if pipeline_route(engine, m)[0].route == "ESCALATE")
    print(f"\nSafety cases sent to a person: {safe}/{len(SAFETY_CASES)}")


if __name__ == "__main__":
    main()
