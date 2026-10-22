# ---------------------------------------------------------------------
# Tenexus
# triage_service.py | Routes tenant requests using classes and methods.
# ---------------------------------------------------------------------

class TriageService:
    def __init__(self):
        self.emergencies = ["gas", "smoke", "fire", "sparks", "flooding"]
        self.maintenance = ["leak", "clog", "broken", "heater", "toilet"]
        self.questions = ["trash", "garbage", "parking"]

    def categorize(self, description):
        message = description.lower()

        if any(word in message for word in self.emergencies):
            return "EMERGENCY"

        if any(word in message for word in self.maintenance):
            return "MAINTENANCE"

        if any(word in message for word in self.questions):
            return "QUESTION"

        return "UNKNOWN"

    def process_request(self, request):
        category = self.categorize(request.description)

        if category == "EMERGENCY":
            request.escalate()
            return "ESCALATE"

        elif category == "MAINTENANCE":
            return "VENDOR"

        elif category == "QUESTION":
            request.answer()
            return "ANSWER"

        request.escalate()
        return "ESCALATE"
