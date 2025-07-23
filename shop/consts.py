from enum import Enum

class DefaultSuperUser:
    """Default superuser info"""

    EMAIL = "noreply.admin@mnory.com"
    NAME = "mnory"
    PASSWORD = "admin123456"  # nosec


class Groups(Enum):
    """User groups"""

    ADMIN = "Admin"
    CUSTOMER = "customer"