"""OBJECT-ORIENTED layer - the business entities and their rules.

Each class guards its own data (encapsulation). A request can only move through
allowed statuses, and only the property's own landlord can review it.
"""
import re

ROUTES = ("ANSWER", "VENDOR", "ESCALATE")
CATEGORIES = ("plumbing", "electrical", "heating", "appliance", "pests",
              "lockout", "safety", "noise", "question")

STATUS_FLOW = {
    "NEW": {"TRIAGED"},
    "TRIAGED": {"ANSWERED", "REFERRED", "ESCALATED"},
    "ANSWERED": {"REVIEWED"},
    "REFERRED": {"REVIEWED"},
    "ESCALATED": {"REVIEWED"},
    "REVIEWED": set(),
}
ROUTE_STATUS = {"ANSWER": "ANSWERED", "VENDOR": "REFERRED", "ESCALATE": "ESCALATED"}

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class DomainError(Exception):
    """A business rule was broken."""


class PermissionDenied(DomainError):
    pass


class Person:
    def __init__(self, person_id, name, email):
        if not name or not name.strip():
            raise DomainError("name is required")
        if not EMAIL.match(email or ""):
            raise DomainError("email is not valid")
        self.id = person_id
        self._name = name.strip()
        self._email = email

    @property
    def name(self):
        return self._name

    @property
    def email(self):
        return self._email


class Landlord(Person):
    pass


class Vendor:
    def __init__(self, name, trade, phone):
        self.name, self.trade, self.phone = name, trade, phone


class Property:
    def __init__(self, property_id, address, landlord):
        self.id = property_id
        self.address = address
        self.landlord = landlord
        self._vendors = []

    def add_vendor(self, vendor):
        self._vendors.append(vendor)

    @property
    def vendors(self):
        return tuple(self._vendors)        # a copy, so callers cannot change our list


class Tenant(Person):
    def __init__(self, person_id, name, email, home):
        super().__init__(person_id, name, email)
        self.home = home                   # the Property this tenant lives in

    def submit(self, message):
        """A tenant can only create requests for their own property."""
        return MaintenanceRequest(self, message)


class MaintenanceRequest:
    def __init__(self, tenant, message):
        if message is None or not (5 <= len(message.strip()) <= 1000):
            raise DomainError("message must be between 5 and 1000 characters")
        self.tenant = tenant
        self.property = tenant.home
        self.message = message.strip()
        self.category = None
        self.confidence = None
        self._status = "NEW"
        self._route = None
        self._landlord_route = None
        self.urgency = None
        self.reason = None
        self.vendor_name = None
        self.vendor_phone = None
        self.answer_text = None
        self.id = None

    @classmethod
    def restore(cls, tenant, row):
        """Rebuild a request from a saved database row (used when a landlord reviews it)."""
        req = cls(tenant, row["message"])
        req.id = row["id"]
        req.category, req.confidence = row["category"], row["confidence"]
        req.urgency, req.reason = row["urgency"], row["reason"]
        req.vendor_name, req.vendor_phone = row["vendor_name"], row["vendor_phone"]
        req.answer_text = row["answer_text"]
        req._status, req._route = row["status"], row["route"]
        req._landlord_route = row["landlord_route"]
        return req

    # -- read-only views of private state --
    @property
    def status(self):
        return self._status

    @property
    def route(self):
        return self._route

    @property
    def landlord_route(self):
        return self._landlord_route

    # -- behaviour --
    def _move_to(self, new_status):
        if new_status not in STATUS_FLOW[self._status]:
            raise DomainError(f"cannot move from {self._status} to {new_status}")
        self._status = new_status

    def record_ai_result(self, category, confidence):
        if category not in CATEGORIES:
            raise DomainError(f"unknown category: {category}")
        if not 0.0 <= confidence <= 1.0:
            raise DomainError("confidence must be between 0 and 1")
        self.category, self.confidence = category, confidence

    def apply_decision(self, decision):
        """Take the functional layer's Decision and update this request."""
        if decision.route not in ROUTES:
            raise DomainError(f"unknown route: {decision.route}")
        self._move_to("TRIAGED")
        self._route = decision.route
        self.urgency = decision.urgency
        self.reason = decision.reason
        self.vendor_name = decision.vendor_name
        self.vendor_phone = decision.vendor_phone
        self.answer_text = decision.answer
        self._move_to(ROUTE_STATUS[decision.route])

    def review(self, landlord, route):
        """The property's landlord approves (same route) or corrects (new route) the AI."""
        if landlord.id != self.property.landlord.id:
            raise PermissionDenied("only the landlord of this property can review it")
        if route not in ROUTES:
            raise DomainError(f"unknown route: {route}")
        self._move_to("REVIEWED")
        self._landlord_route = route
