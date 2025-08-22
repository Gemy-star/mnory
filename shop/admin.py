from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import PermissionDenied

from .models import MnoryUser, VendorProfile, Product, Order, Cart, Wishlist, ShippingAddress, Payment


class CustomAdminSite(AdminSite):
    site_header = "Mnory Platform Admin"
    site_title = "Mnory Admin"
    index_title = "Welcome to Mnory Admin"

    def has_permission(self, request):
        """Allow only authenticated users into admin."""
        return request.user.is_active and request.user.is_authenticated

    def get_app_list(self, request):
        """Filter apps and models based on user_type."""
        app_list = super().get_app_list(request)

        user = request.user

        # Super admin → full access
        if user.is_superuser or user.is_admin_user:
            return app_list

        # Vendor → Only product-related models
        if user.is_vendor_user:
            allowed_models = {"Product", "VendorProfile"}
        
        # Customer → Only order/cart/wishlist/shipping/payment
        elif user.is_customer_user:
            allowed_models = {"Order", "Cart", "Wishlist", "ShippingAddress", "Payment"}

        # Company/Freelancer/Affiliate → customize as needed
        elif user.is_company_user or user.is_freelancer_user or user.is_affiliate_user:
            allowed_models = {"Order"}  # Example: only orders

        else:
            allowed_models = set()

        # Filter visible models
        filtered = []
        for app in app_list:
            app["models"] = [m for m in app["models"] if m["object_name"] in allowed_models]
            if app["models"]:
                filtered.append(app)

        return filtered


# -----------------------------
# Custom Admin Classes
# -----------------------------

@admin.register(MnoryUser, site=CustomAdminSite(name="custom_admin"))
class MnoryUserAdmin(admin.ModelAdmin):
    list_display = ("email", "user_type", "is_active", "is_staff")
    search_fields = ("email", "phone_number")
    list_filter = ("user_type", "is_active", "is_staff")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_admin_user:
            return qs
        # Vendors/Customers shouldn't see user list
        raise PermissionDenied


@admin.register(Product, site=CustomAdminSite(name="custom_admin"))
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "vendor", "price")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_admin_user:
            return qs
        elif request.user.is_vendor_user:
            return qs.filter(vendor__user=request.user)
        return qs.none()

    def save_model(self, request, obj, form, change):
        if request.user.is_vendor_user and not change:
            obj.vendor = VendorProfile.objects.get(user=request.user)
        super().save_model(request, obj, form, change)


@admin.register(Order, site=CustomAdminSite(name="custom_admin"))
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "payment_status")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_admin_user:
            return qs
        elif request.user.is_customer_user:
            return qs.filter(user=request.user)
        return qs.none()

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_customer_user:
            return ["status", "payment_status", "user"]
        return super().get_readonly_fields(request, obj)


@admin.register(Cart, site=CustomAdminSite(name="custom_admin"))
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_customer_user:
            return qs.filter(user=request.user)
        return qs.none()


@admin.register(Wishlist, site=CustomAdminSite(name="custom_admin"))
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("id", "user")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_customer_user:
            return qs.filter(user=request.user)
        return qs.none()


@admin.register(ShippingAddress, site=CustomAdminSite(name="custom_admin"))
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ("user", "city", "country")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_customer_user:
            return qs.filter(user=request.user)
        return qs.none()


@admin.register(Payment, site=CustomAdminSite(name="custom_admin"))
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "amount", "status")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_customer_user:
            return qs.filter(user=request.user)
        return qs.none()
