"""
Custom authentication backend for Mnory
Handles role-based redirects after login
"""

from django.contrib.auth.backends import ModelBackend
from django.urls import reverse


class RoleBasedRedirectBackend(ModelBackend):
    """
    Custom authentication backend that determines redirect URL based on user role
    """

    def get_user_redirect_url(self, user):
        """
        Return the appropriate dashboard URL based on user type

        Priority order:
        1. Vendor → Vendor dashboard
        2. Freelancer → Freelancer dashboard
        3. Company → Company dashboard
        4. Customer → User profile
        5. Admin/Superuser → Custom Admin Dashboard
        6. Default → Home page
        """
        if getattr(user, "is_vendor_type", False):
            return reverse("shop:vendor_dashboard")

        if getattr(user, "is_freelancer_type", False):
            return reverse("freelancer_dashboard")

        if getattr(user, "is_company_type", False):
            return reverse("company_dashboard")

        if getattr(user, "is_customer_type", False):
            return reverse("shop:profile")

        if user.is_superuser or getattr(user, "is_admin_type", False):
            return reverse("shop:admin_dashboard")

        # Fallback to home page
        return reverse("shop:home")
