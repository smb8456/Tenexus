"""OBJECT-ORIENTED layer: classes, encapsulation, status rules, permissions."""
import unittest

from models import (DomainError, Landlord, MaintenanceRequest, PermissionDenied,
                    Property, Tenant, Vendor)
from scoring import Decision


def make_world():
    ana = Landlord(1, "Ana Rivera", "ana@example.com")
    jo = Landlord(2, "Jo Park", "jo@example.com")
    prop = Property(1, "1420 Spruce St", ana)
    sam = Tenant(1, "Sam Carter", "sam@example.com", prop)
    return ana, jo, prop, sam


def triaged(sam, route="VENDOR"):
    req = sam.submit("My sink is leaking badly")
    req.record_ai_result("plumbing", 0.8)
    req.apply_decision(Decision(route, 5, "test"))
    return req


class ModelTests(unittest.TestCase):
    def test_tenant_request_belongs_to_tenants_own_property(self):
        _, _, prop, sam = make_world()
        self.assertIs(sam.submit("My sink is leaking").property, prop)

    def test_only_the_properties_landlord_can_review(self):
        ana, jo, _, sam = make_world()
        req = triaged(sam)
        with self.assertRaises(PermissionDenied):
            req.review(jo, "VENDOR")
        req.review(ana, "VENDOR")
        self.assertEqual(req.status, "REVIEWED")

    def test_status_follows_the_allowed_flow(self):
        ana, _, _, sam = make_world()
        req = sam.submit("My sink is leaking")
        with self.assertRaises(DomainError):
            req.review(ana, "VENDOR")                 # NEW -> REVIEWED is not allowed
        req.apply_decision(Decision("ESCALATE", 8, "x"))
        self.assertEqual(req.status, "ESCALATED")
        with self.assertRaises(DomainError):
            req.apply_decision(Decision("ANSWER", 1, "x"))   # cannot triage twice

    def test_a_request_can_only_be_reviewed_once(self):
        ana, _, _, sam = make_world()
        req = triaged(sam)
        req.review(ana, "VENDOR")
        with self.assertRaises(DomainError):
            req.review(ana, "ESCALATE")

    def test_status_and_route_are_read_only(self):
        _, _, _, sam = make_world()
        req = triaged(sam)
        with self.assertRaises(AttributeError):
            req.status = "REVIEWED"
        with self.assertRaises(AttributeError):
            req.route = "ANSWER"

    def test_property_hands_out_a_copy_of_its_vendors(self):
        _, _, prop, _ = make_world()
        prop.add_vendor(Vendor("Liberty Plumbing", "plumber", "555-0101"))
        snapshot = prop.vendors
        prop.add_vendor(Vendor("Brightside Electric", "electrician", "555-0102"))
        self.assertEqual(len(snapshot), 1)
        self.assertEqual(len(prop.vendors), 2)
        self.assertIsInstance(snapshot, tuple)

    def test_short_message_is_rejected(self):
        _, _, _, sam = make_world()
        with self.assertRaises(DomainError):
            sam.submit("hi")

    def test_bad_email_and_blank_name_are_rejected(self):
        ana, _, prop, _ = make_world()
        with self.assertRaises(DomainError):
            Tenant(9, "Pat", "not-an-email", prop)
        with self.assertRaises(DomainError):
            Tenant(9, "   ", "pat@example.com", prop)

    def test_unknown_category_and_route_are_rejected(self):
        ana, _, _, sam = make_world()
        req = sam.submit("My sink is leaking")
        with self.assertRaises(DomainError):
            req.record_ai_result("weather", 0.5)
        with self.assertRaises(DomainError):
            req.record_ai_result("plumbing", 1.5)
        req = triaged(sam)
        with self.assertRaises(DomainError):
            req.review(ana, "MAYBE")


if __name__ == "__main__":
    unittest.main()
