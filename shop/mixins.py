# shop/mixins.py
from django.contrib import admin
from django.core.exceptions import PermissionDenied


class AdminVendorCustomerOnlyMixin:
    """Mixin to restrict admin access to admin, vendor, and customer users only"""

    def has_module_permission(self, request):
        return (
                request.user.is_authenticated and
                request.user.is_active and
                (request.user.is_superuser or
                 request.user.is_admin_type or
                 request.user.is_vendor_type or
                 request.user.is_customer_type)
        )

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_module_permission(request)


class AdminOnlyMixin:
    """Mixin to restrict admin access to admin users only"""

    def has_module_permission(self, request):
        return (
                request.user.is_authenticated and
                (request.user.is_superuser or request.user.is_admin_type)
        )

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_module_permission(request)


class VendorFilterMixin:
    """Mixin to filter queryset for vendor users"""

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_admin_type:
            return qs
        elif request.user.is_vendor_type:
            return qs.filter(vendor__user=request.user)
        return qs.none()


class CustomerFilterMixin:
    """Mixin to filter queryset for customer users"""

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_admin_type:
            return qs
        elif request.user.is_customer_type:
            return qs.filter(user=request.user)
        return qs.none()


class UserRestrictedMixin:
    """Mixin to restrict users from seeing user list unless admin"""

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_admin_type:
            return qs
        raise PermissionDenied


class CustomerReadOnlyMixin:
    """Mixin to make certain fields read-only for customers"""

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if request.user.is_customer_type:
            readonly_fields.extend(["status", "payment_status", "user"])
        return readonly_fields


class VendorAutoAssignMixin:
    """Mixin to auto-assign vendor profile when vendor creates products"""

    def save_model(self, request, obj, form, change):
        if request.user.is_vendor_type and not change and hasattr(obj, 'vendor'):
            from .models import VendorProfile
            obj.vendor = VendorProfile.objects.get(user=request.user)
        super().save_model(request, obj, form, change)
