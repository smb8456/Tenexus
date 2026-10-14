
# ---------------------------------------------------------------------
# Tenexus
# test_prototypes.py | Tests Tenexus models and request-routing prototypes.
# ---------------------------------------------------------------------

import pytest

from src.models.tenant import Tenant
from src.models.landlord import Landlord
from src.models.property import Property
from src.models.vendor import Vendor
from src.prototypes.imperative.workflow import process_request
from src.prototypes.object_oriented.triage_service import TriageService


cases = [
    ("My kitchen sink is leaking", "VENDOR"),
    ("I smell gas in my apartment", "ESCALATE"),
    ("When is trash day?", "ANSWER"),
    ("My heater is broken", "VENDOR"),
    ("I need help with my lease", "ESCALATE"),
    ("There is smoke and a leak", "ESCALATE"),
]


@pytest.mark.parametrize("description,expected", cases)
def test_imperative(description, expected):
    assert process_request(description) == expected


@pytest.mark.parametrize("description,expected", cases)
def test_object_oriented(description, expected):
    tenant = Tenant("Jane", "jane@email.com")
    request = tenant.submit_request(description)

    triage = TriageService()
    assert triage.process_request(request) == expected


def test_models():
    landlord = Landlord("John", "john@email.com")
    property = Property("123 Main Street", landlord)
    tenant = Tenant("Jane", "jane@email.com")
    vendor = Vendor("ABC Plumbing", "Plumbing")

    landlord.add_property(property)
    property.add_tenant(tenant)

    request = tenant.submit_request("Sink is leaking")
    vendor.assign_request(request)

    assert property in landlord.properties
    assert tenant in property.tenants
    assert request in tenant.requests
    assert request.vendor is vendor
    assert request.status == "Assigned"


def test_request_status():
    tenant = Tenant("Jane", "jane@email.com")
    request = tenant.submit_request("I smell gas")

    request.escalate()
    assert request.status == "Escalated"

    request.complete()
    assert request.status == "Completed"
