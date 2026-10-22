"""IMPERATIVE layer - the ordered, step-by-step workflow for every request.

Explicit sequence, mutable state (the audit trail list), conditions and loops.
The ten steps are always run in this order and each one is logged.
"""
from models import DomainError, PermissionDenied
from scoring import Context, VendorInfo, decide


class ValidationError(Exception):
    pass


class NotFound(Exception):
    pass


def process_request(repo, ai, tenant_id, message):
    audit = []                                  # state that grows as we go

    def log(step, name, detail):
        audit.append((step, name, detail))

    # 1. Receive
    log(1, "Receive request", f"tenant id {tenant_id!r}")

    # 2. Validate
    if not isinstance(message, str) or not message.strip():
        raise ValidationError("Please describe the problem.")
    text = message.strip()
    if len(text) < 5:
        raise ValidationError("Message is too short (at least 5 characters).")
    if len(text) > 1000:
        raise ValidationError("Message is too long (at most 1000 characters).")
    if isinstance(tenant_id, bool) or not isinstance(tenant_id, int):
        raise ValidationError("tenant_id must be a whole number.")
    tenant = repo.load_tenant(tenant_id)
    if tenant is None:
        raise NotFound("That tenant account does not exist.")
    log(2, "Validate input", "message length and tenant account are valid")

    # 3. Normalize whitespace
    text = " ".join(text.split())
    log(3, "Normalize message", f"{len(text)} characters")

    # 4. Create the domain object (object-oriented layer)
    request = tenant.submit(text)
    log(4, "Create MaintenanceRequest", f"for {tenant.home.address}")

    # 5. AI classification
    category, confidence = ai.classify(text)
    request.record_ai_result(category, confidence)
    log(5, "AI classification", f"{category} ({confidence:.2f})")

    # 6. FAQ search, only for questions
    faq_answer = None
    if category == "question":
        faq_answer = ai.best_faq(text, repo.faqs_for(tenant.home.id))
        log(6, "Search approved FAQ", "match found" if faq_answer else "no approved answer found")
    else:
        log(6, "Search approved FAQ", "skipped (not a question)")

    # 7. Decide the route (functional layer)
    vendors = tuple(VendorInfo(v.name, v.trade, v.phone) for v in tenant.home.vendors)
    decision = decide(Context(text, category, confidence, faq_answer, vendors))
    log(7, "Decide route", f"{decision.route}: {decision.reason}")

    # 8. Apply the decision to the request
    request.apply_decision(decision)
    log(8, "Update request status", request.status)

    # 9. Save (declarative SQL layer)
    request_id = repo.save_request(request)
    log(9, "Save request", f"stored as request #{request_id}")

    # 10. Alert / finish
    if decision.route == "ESCALATE":
        alert = f"landlord alert queued for {tenant.home.landlord.name}"
        if decision.guardrail:
            alert += "; tenant shown emergency guidance"
    elif decision.route == "VENDOR":
        alert = f"vendor referral shown to tenant; landlord can review"
    else:
        alert = "approved FAQ answer shown to tenant"
    log(10, "Notify", alert)

    repo.save_audit(request_id, audit)

    return {
        "id": request_id,
        "route": request.route,
        "status": request.status,
        "category": category,
        "confidence": round(confidence, 3),
        "urgency": request.urgency,
        "reason": request.reason,
        "vendor_name": request.vendor_name,
        "vendor_phone": request.vendor_phone,
        "answer": request.answer_text,
        "guardrail": decision.guardrail,
        "needs_review": decision.needs_review,
        "tenant_message": tenant_message(request.route, request.reason, request.category,
                                         request.answer_text, request.vendor_name, request.vendor_phone),
        "audit": [{"step": s, "name": n, "detail": d} for s, n, d in audit],
    }


def tenant_message(route, reason, category, answer, vendor_name, vendor_phone):
    """The plain-language text the tenant sees."""
    emergency = reason.startswith("Safety keyword") or category == "safety"
    if route == "ANSWER":
        return answer
    if route == "VENDOR":
        return (f"Please contact {vendor_name} at {vendor_phone}. "
                "Your landlord can review this referral.")
    text = "Your landlord has been alerted and will follow up."
    if emergency:
        text = ("If anyone is in danger, or you smell gas or see smoke or fire, leave the area and call 911. "
                + text)
    return text


def review_request(repo, request_id, landlord_id, route):
    """A landlord approves or corrects the AI's route."""
    request = repo.load_request(request_id)
    if request is None:
        raise NotFound("That request does not exist.")
    landlord = repo.load_landlord(landlord_id)
    if landlord is None:
        raise NotFound("That landlord account does not exist.")
    request.review(landlord, route)             # raises PermissionDenied / DomainError
    repo.save_review(request)
    return request
