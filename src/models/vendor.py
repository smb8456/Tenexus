# ---------------------------------------------------------------------
# Tenexus
# vendor.py
# ---------------------------------------------------------------------

class Vendor:
    def __init__(self, name, specialty):
        self.name = name
        self.specialty = specialty
        self.requests = []

    def assign_request(self, request):
        request.assign_vendor(self)
        self.requests.append(request)