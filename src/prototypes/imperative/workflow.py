
# Tenexus - Imperative Programming Prototype
# Processes tenant requests using variables, loops, and conditions.


def process_request(description):
    # Convert the request to lowercase.
    message = description.lower()

    # Keywords used to categorize requests.
    emergencies = ["gas", "smoke", "fire", "sparks", "flooding"]
    maintenance = ["leak", "clog", "broken", "heater", "toilet"]
    questions = ["trash", "garbage", "parking"]

    # Default routing decision.
    decision = "ESCALATE"

    # Check for emergencies first.
    for word in emergencies:
        if word in message:
            decision = "ESCALATE"
            break
    else:
        # Check for maintenance problems.
        for word in maintenance:
            if word in message:
                decision = "VENDOR"
                break
        else:
            # Check for common questions.
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

    # Process each request.
    for request in requests:
        decision = process_request(request)

        print("Request:", request)
        print("Decision:", decision)
        print()


if __name__ == "__main__":
    main()
