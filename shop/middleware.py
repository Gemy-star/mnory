# middleware.py
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import gettext as _


class AdminAccessMiddleware(MiddlewareMixin):
    """
    Middleware to control admin access based on user type
    """

    def process_request(self, request):
        # Check if this is an admin URL
        if request.path.startswith("/admin/"):
            # Allow login and logout pages
            if request.path in ["/admin/login/", "/admin/logout/"]:
                return None

            # Check if user is authenticated
            if not request.user.is_authenticated:
                return None  # Let Django handle redirect to login

            # Get user type
            user_type = getattr(request.user, "user_type", None)

            # Allow superusers and staff
            if request.user.is_superuser or request.user.is_staff:
                return None

            # Check if user has allowed user_type for admin access
            allowed_user_types = ["vendor", "customer", "client"]
            if user_type not in allowed_user_types:
                messages.error(
                    request, "You do not have permission to access the admin panel."
                )
                logout(request)
                return redirect("admin:login")

            # Additional check for vendor approval
            if user_type == "vendor":
                try:
                    from shop.models import VendorProfile

                    vendor_profile = VendorProfile.objects.get(user=request.user)
                    if not vendor_profile.is_approved:
                        messages.warning(
                            request,
                            "Your vendor account is pending approval. Some features may be limited.",
                        )
                except VendorProfile.DoesNotExist:
                    if "/admin/shop/vendorprofile/add/" not in request.path:
                        messages.info(
                            request, "Please complete your vendor profile setup."
                        )
                        return redirect("/admin/shop/vendorprofile/add/")

        return None


class UserTypeContextMiddleware(MiddlewareMixin):
    """
    Middleware to add user type context to all requests
    """

    def process_request(self, request):
        if request.user.is_authenticated:
            request.user_type = getattr(request.user, "user_type", "admin")
            request.is_vendor = request.user_type == "vendor"
            request.is_customer = request.user_type in ["customer", "client"]
            request.is_admin = request.user.is_superuser or request.user.is_staff
        else:
            request.user_type = None
            request.is_vendor = False
            request.is_customer = False
            request.is_admin = False

        return None


class LoginRedirectMiddleware(MiddlewareMixin):
    """
    Middleware to redirect authenticated users accessing login page or admin index
    to their appropriate dashboard based on user type
    """

    def process_request(self, request):
        # Only process for authenticated users
        if not request.user.is_authenticated:
            return None

        # Get the current path
        path = request.path

        # Paths to intercept for non-admin users
        admin_paths = [
            "/admin/",
            "/admin/login/",
        ]

        login_paths = [
            reverse("shop:login"),
        ]

        # Check if non-admin user is trying to access admin
        is_admin_user = request.user.is_superuser or getattr(
            request.user, "is_admin_type", False
        )

        # Redirect non-admin users away from admin area
        if not is_admin_user and any(
            path.startswith(admin_path) for admin_path in admin_paths
        ):
            redirect_url = self._get_user_dashboard(request.user)
            messages.warning(
                request, _("You don't have permission to access the admin area.")
            )
            return redirect(redirect_url)

        # Redirect authenticated users away from login page
        if path in login_paths:
            redirect_url = self._get_user_dashboard(request.user)
            if redirect_url and redirect_url != path:
                return redirect(redirect_url)

        return None

    def _get_user_dashboard(self, user):
        """Get the appropriate dashboard URL for the user"""
        # Check user type flags
        if getattr(user, "is_vendor_type", False):
            return reverse("shop:vendor_dashboard")

        if getattr(user, "is_freelancer_type", False):
            return reverse("freelancer_dashboard")

        if getattr(user, "is_company_type", False):
            return reverse("company_dashboard")

        if getattr(user, "is_customer_type", False):
            return reverse("shop:profile")

        if user.is_superuser or getattr(user, "is_admin_type", False):
            # Admin/superusers go to Django admin
            return "/admin/"

        # Default fallback
        return reverse("shop:home")
