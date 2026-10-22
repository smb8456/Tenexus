
# Tenexus - Imperative Programming Prototype
# Processes tenant requests using variables, loops, and conditions.


def process_request(description):
    message = description.lower()

    emergencies = ["gas", "smoke", "fire", "sparks", "flooding"]
    maintenance = ["leak", "clog", "broken", "heater", "toilet"]
    questions = ["trash", "garbage", "parking"]

    decision = "ESCALATE"

    for word in emergencies:
        if word in message:
            return "ESCALATE"

    for word in maintenance:
        if word in message:
            decision = "VENDOR"
            break

    if decision == "ESCALATE":
        for word in questions:
            if word in message:
                decision = "ANSWER"
                break

    return decision


def main():
    requests = [
        "My kitchen sink is leaking",
        "I smell gas in my apartment",
        "When is trash day?",
        "My heater is broken",
        "I need help with my lease"
    ]

    for request in requests:
        print("Request:", request)
        print("Decision:", process_request(request))
        print()


if __name__ == "__main__":
    main()
