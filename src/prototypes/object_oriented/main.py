
from src.models.tenant import Tenant
from src.models.vendor import Vendor
from src.prototypes.object_oriented.triage_service import TriageService


def main():
    tenant = Tenant("Jane Doe", "jane@email.com")
    vendor = Vendor("ABC Plumbing", "Plumbing")
    triage = TriageService()

    descriptions = [
        "My kitchen sink is leaking",
        "I smell gas in my apartment",
        "When is trash day?",
        "My heater is broken",
        "I need help with my lease"
    ]

    for description in descriptions:
        request = tenant.submit_request(description)
        decision = triage.process_request(request)

        if decision == "VENDOR":
            vendor.assign_request(request)

        print("Request:", request.description)
        print("Decision:", decision)
        print("Status:", request.status)
        print()


if __name__ == "__main__":
    main()
