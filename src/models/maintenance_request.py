# ---------------------------------------------------------------------
# Tenexus
# maintenance_request.py
# ---------------------------------------------------------------------

class MaintenanceRequest:
    def __init__(self, tenant, description):
        self.tenant = tenant
        self.description = description
        self.status = "Pending"
        self.vendor = None

    def assign_vendor(self, vendor):
        self.vendor = vendor
        self.status = "Assigned"

    def escalate(self):
        self.status = "Escalated"

    def answer(self):
        self.status = "Answered"

    def complete(self):
        self.status = "Completed"
