# ---------------------------------------------------------------------
# Tenexus
# property.py
# ---------------------------------------------------------------------

class Property:
    def __init__(self, address, landlord):
        self.address = address
        self.landlord = landlord
        self.tenants = []

    def add_tenant(self, tenant):
        self.tenants.append(tenant)
