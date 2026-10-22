"""FUNCTIONAL layer - decides the route for one request.

Pure functions only: the same input always gives the same output, nothing is
changed in place, no global state. Data is immutable (frozen dataclasses and
tuples). Rules are small functions; the first rule that returns a Decision wins.
"""
from dataclasses import dataclass
from functools import reduce
from types import MappingProxyType
from typing import Optional

CONFIDENCE_THRESHOLD = 0.35

SAFETY_WORDS = ("gas", "smoke", "fire", "spark", "carbon monoxide", "burning")
LOCKOUT_WORDS = ("locked out", "lockout", "lost my key", "lost key", "locked myself out")
URGENT_WORDS = ("emergency", "flood", "burst", "overflow", "urgent", "right now", "freezing")

BASE_URGENCY = MappingProxyType({
    "safety": 10, "lockout": 8, "heating": 6, "electrical": 5, "plumbing": 5,
    "appliance": 3, "pests": 3, "noise": 3, "question": 1,
})
VENDOR_TRADE = MappingProxyType({
    "plumbing": "plumber", "electrical": "electrician", "heating": "hvac",
    "appliance": "appliance", "pests": "pest",
})


@dataclass(frozen=True)
class VendorInfo:
    name: str
    trade: str
    phone: str


@dataclass(frozen=True)
class Context:
    message: str
    category: str
    confidence: float
    faq_answer: Optional[str]
    vendors: tuple


@dataclass(frozen=True)
class Decision:
    route: str                      # ANSWER, VENDOR or ESCALATE
    urgency: int                    # 0-10
    reason: str
    vendor_name: Optional[str] = None
    vendor_phone: Optional[str] = None
    answer: Optional[str] = None
    guardrail: bool = False         # True when a safety/lockout keyword forced the route
    needs_review: bool = True       # a person should look unless it is a simple FAQ


# ---------- small pure helpers ----------

def hits(text, words):
    """Which of the words appear in the text (a new tuple each time)."""
    lowered = text.lower()
    return tuple(filter(lambda w: w in lowered, words))


def urgency_for(ctx):
    """Base urgency for the category, plus one boost of 2 for urgent wording, capped at 10."""
    base = BASE_URGENCY.get(ctx.category, 5)
    boost = 2 if hits(ctx.message, URGENT_WORDS) else 0
    return min(10, base + boost)


def pick_vendor(category, vendors):
    trade = VENDOR_TRADE.get(category)
    return next(filter(lambda v: v.trade == trade, vendors), None)


# ---------- rules: Context -> Optional[Decision] ----------

def safety_guardrail(ctx):
    found = hits(ctx.message, SAFETY_WORDS)
    if found:
        return Decision("ESCALATE", 10, f"Safety keyword: {found[0]}", guardrail=True)


def lockout_guardrail(ctx):
    found = hits(ctx.message, LOCKOUT_WORDS)
    if found:
        return Decision("ESCALATE", 8, "Lockout", guardrail=True)


def low_confidence(ctx):
    if ctx.confidence < CONFIDENCE_THRESHOLD:
        return Decision("ESCALATE", urgency_for(ctx), "AI confidence below threshold")


def high_urgency(ctx):
    urgency = urgency_for(ctx)
    if urgency >= 8:
        return Decision("ESCALATE", urgency, f"High urgency ({ctx.category})")


def approved_faq(ctx):
    if ctx.category == "question" and ctx.faq_answer:
        return Decision("ANSWER", 1, "Matched an approved FAQ answer",
                        answer=ctx.faq_answer, needs_review=False)


def known_vendor(ctx):
    vendor = pick_vendor(ctx.category, ctx.vendors)
    if vendor:
        return Decision("VENDOR", urgency_for(ctx), f"Referred to {vendor.trade}",
                        vendor_name=vendor.name, vendor_phone=vendor.phone)


RULES = (safety_guardrail, lockout_guardrail, low_confidence,
         high_urgency, approved_faq, known_vendor)


def fallback(ctx):
    return Decision("ESCALATE", urgency_for(ctx), "No safe automatic route; landlord decides")


def decide(ctx):
    """First rule that returns a Decision wins (map is lazy, so later rules are skipped)."""
    return next(filter(None, map(lambda rule: rule(ctx), RULES)), fallback(ctx))


def route_counts(decisions):
    """Count routes with reduce: builds a new dict each step instead of changing one."""
    return reduce(lambda acc, d: {**acc, d.route: acc.get(d.route, 0) + 1}, decisions, {})
