# ---------------------------------------------------------------------
# Tenexus
# landlord.py
# ---------------------------------------------------------------------

class Landlord:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.properties = []

    def add_property(self, property):
        self.properties.append(property)