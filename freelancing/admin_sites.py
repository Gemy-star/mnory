from django.contrib.admin import AdminSite
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

class FreelancingAdminSite(AdminSite):
    site_header = "Mnory Freelancing Admin"
    site_title = "Freelancing Admin"
    index_title = "Welcome to Freelancing Admin"


    def has_permission(self, request):
        user = request.user
        return (
            user.is_authenticated
            and user.is_active
            and (
                user.is_superuser
                or getattr(user, "is_admin_type", False)
                or getattr(user, "is_company_type", False)
                or getattr(user, "is_freelancer_type", False)
            )
        )

    def login(self, request, extra_context=None):
        """Redirect freelancing admin login to global /login/"""
        return redirect(reverse("shop:login"))

    def get_app_list(self, request):
        """Filter apps and models based on user_type."""
        user = request.user

        # 🚨 If not logged in → return empty (Django will already redirect to login)
        if not user.is_authenticated:
            return []

        app_list = super().get_app_list(request)

        # Super admin or admin → full access
        if user.is_superuser or getattr(user, "is_admin_type", False):
            return app_list

        # Company → Project-related models
        if getattr(user, "is_company_type", False):
            allowed_models = {"Project", "CompanyProfile", "Contract", "Payment", "Review", "Message", "Notification"}

        # Freelancer → Freelancer-related models
        elif getattr(user, "is_freelancer_type", False):
            allowed_models = {"FreelancerProfile", "Proposal", "Contract", "Payment", "Review", "Message", "Notification"}

        else:
            allowed_models = set()

        # Filter visible models
        filtered = []
        for app in app_list:
            app["models"] = [m for m in app["models"] if m["object_name"] in allowed_models]
            if app["models"]:
                filtered.append(app)

        return filtered


# Create freelancing admin site instance
freelancing_admin_site = FreelancingAdminSite(name="freelancing_admin")
