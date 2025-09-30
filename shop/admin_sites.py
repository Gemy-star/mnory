from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _

class ShopAdminSite(AdminSite):
    site_header = "Mnory Shop Admin"
    site_title = "Shop Admin"
    index_title = "Welcome to Shop Admin"

    def has_permission(self, request):
        """Allow only authenticated users with specific user types into admin."""
        user = request.user

        if not user.is_authenticated:
            return False  # Django will auto-redirect to login

        return (
            user.is_active and (
                user.is_superuser or
                getattr(user, "is_admin_type", False) or
                getattr(user, "is_vendor_type", False) or
                getattr(user, "is_customer_type", False)
            )
        )

    def get_app_list(self, request):
        """Filter apps and models based on user_type."""
        app_list = super().get_app_list(request)
        user = request.user

        # Super admin or admin → full access
        if user.is_superuser or getattr(user, "is_admin_type", False):
            return app_list

        # Vendor → Only product-related models
        if getattr(user, "is_vendor_type", False):
            allowed_models = {"Product", "VendorProfile"}

        # Customer → Only order/cart/wishlist/shipping/payment
        elif getattr(user, "is_customer_type", False):
            allowed_models = {"Order", "Cart", "Wishlist", "ShippingAddress", "Payment"}

        else:
            allowed_models = set()

        # Filter visible models
        filtered = []
        for app in app_list:
            app["models"] = [m for m in app["models"] if m["object_name"] in allowed_models]
            if app["models"]:
                filtered.append(app)

        return filtered

# Create shop admin site instance
shop_admin_site = ShopAdminSite(name="shop_admin")
