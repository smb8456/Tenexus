# ---------------------------------------------------------------------
# Tenexus
# tenant.py
# ---------------------------------------------------------------------

from .maintenance_request import MaintenanceRequest

class Tenant:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.requests = []

    def submit_request(self, description):
        request = MaintenanceRequest(self, description)
        self.requests.append(request)
        return request