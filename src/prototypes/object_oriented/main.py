from src.models.tenant import Tenant
from src.prototypes.object_oriented.triage_service import TriageService

def main():
    tenant = Tenant("Jane Doe", "jane@email.com")
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

        print("Request:", request.description)
        print("Decision:", decision)
        print()


if __name__ == "__main__":
    main()
