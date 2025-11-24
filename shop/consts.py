from enum import Enum

class DefaultSuperUser:
    """Default superuser info"""

    EMAIL = "noreply.admin@mnory.com"
    NAME = "mnory"
    PASSWORD = "admin123456"  # nosec


class Groups(Enum):
    """User groups"""

    ADMIN = "Admin"
    CUSTOMER = "Customer"
    VENDOR = "Vendor"
    COMPANY = "Company"
    FREELANCER = "Freelancer"
    AFFILIATE = "Affiliate"


# Mapping from user_type to group name
USER_TYPE_TO_GROUP = {
    "admin": Groups.ADMIN.value,
    "customer": Groups.CUSTOMER.value,
    "vendor": Groups.VENDOR.value,
    "company": Groups.COMPANY.value,
    "freelancer": Groups.FREELANCER.value,
    "affiliate": Groups.AFFILIATE.value,
}


def get_group_for_user_type(user_type):
    """Get the group name for a given user type"""
    return USER_TYPE_TO_GROUP.get(user_type)
