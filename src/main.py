
from models.tenant import Tenant
from models.landlord import Landlord
from models.property import Property
from models.vendor import Vendor


def main():
    # Create landlord and property.
    landlord = Landlord("John Smith", "john@email.com")
    property = Property("123 Main Street", landlord)
    landlord.add_property(property)

    # Create tenant.
    tenant = Tenant("Jane Doe", "jane@email.com")
    property.add_tenant(tenant)

    # Create vendor.
    vendor = Vendor("ABC Plumbing", "Plumbing")

    # Tenant submits request.
    request = tenant.submit_request("Kitchen sink is leaking")

    # Assign maintenance vendor.
    vendor.assign_request(request)

    # Display information.
    print("Landlord:", landlord.name)
    print("Property:", property.address)
    print("Tenant:", tenant.name)
    print("Request:", request.description)
    print("Vendor:", request.vendor.name)
    print("Status:", request.status)


if __name__ == "__main__":
    main()