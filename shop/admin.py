from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied

from shop.models import (
    Category, SubCategory, FitType, Brand, Color, Size,
    Product, ProductImage, ProductColor, ProductSize, ProductVariant,
    HomeSlider, Cart, CartItem, Wishlist, WishlistItem,
    Order, OrderItem, ShippingAddress, Payment, MnoryUser, VendorProfile
)
from .forms import MnoryUserChangeForm, MnoryUserCreationForm


# Custom Admin Site for different user types
class CustomAdminSite(admin.AdminSite):
    site_header = "Mnory Shop Administration"
    site_title = "Mnory Admin"
    index_title = "Welcome to Mnory Administration"

    def has_permission(self, request):
        """
        Allow access to admin for staff users and specific user types
        """
        return (
                request.user.is_active and
                (request.user.is_staff or
                 getattr(request.user, 'user_type', None) in ['vendor', 'customer', 'client'])
        )


# Create custom admin site instance
custom_admin_site = CustomAdminSite(name='custom_admin')


# Mixin for filtering based on user type
class UserTypePermissionMixin:
    def get_user_type(self, request):
        return getattr(request.user, 'user_type', 'admin')

    def is_admin(self, request):
        return request.user.is_superuser or request.user.is_staff

    def is_vendor(self, request):
        return self.get_user_type(request) == 'vendor'

    def is_customer(self, request):
        return self.get_user_type(request) in ['customer', 'client']


@admin.register(MnoryUser)
class MnoryUserAdmin(UserAdmin, UserTypePermissionMixin):
    """
    Admin configuration for the custom MnoryUser model.
    """
    form = MnoryUserChangeForm
    add_form = MnoryUserCreationForm

    list_display = (
        'username', 'email', 'phone_number', 'user_type',
        'is_staff', 'is_active', 'date_joined',
    )
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'user_type', 'groups',)
    search_fields = ('username', 'email', 'phone_number')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'user_type')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone_number', 'user_type', 'password', 'password2'),
        }),
    )
    ordering = ('username',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self.is_admin(request):
            return qs
        # Non-admin users can only see their own profile
        return qs.filter(id=request.user.id)

    def has_change_permission(self, request, obj=None):
        if self.is_admin(request):
            return True
        # Users can only edit their own profile
        return obj is None or obj.id == request.user.id

    def has_delete_permission(self, request, obj=None):
        # Only admins can delete users
        return self.is_admin(request)

    def has_add_permission(self, request):
        # Only admins can add users
        return self.is_admin(request)


@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin, UserTypePermissionMixin):
    """
    Admin configuration for the VendorProfile model.
    """
    list_display = (
        'user', 'store_name', 'profile_type', 'is_approved',
        'product_count', 'wallet_balance', 'country_of_operation',
    )
    list_filter = ('profile_type', 'is_approved', 'country_of_operation',)
    search_fields = ('user__username', 'user__email', 'store_name', 'store_description',)

    readonly_fields = ('logo_resized', 'product_count', 'slug', 'wallet_balance',)

    fieldsets = (
        (None, {
            'fields': ('user', 'store_name', 'store_description', 'logo',
                       'website', 'country_of_operation', 'profile_type', 'is_approved'),
        }),
        ('Advanced Information', {
            'fields': ('product_count', 'wallet_balance', 'logo_resized', 'slug'),
            'classes': ('collapse',),
        }),
    )

    actions = ['make_approved', 'make_not_approved']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self.is_admin(request):
            return qs
        elif self.is_vendor(request):
            # Vendors can only see their own profile
            return qs.filter(user=request.user)
        else:
            # Customers cannot see vendor profiles
            return qs.none()

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        if self.is_vendor(request):
            # Vendors cannot change approval status
            readonly_fields.append('is_approved')
        return readonly_fields

    def has_change_permission(self, request, obj=None):
        if self.is_admin(request):
            return True
        elif self.is_vendor(request):
            return obj is None or obj.user == request.user
        return False

    def has_delete_permission(self, request, obj=None):
        return self.is_admin(request)

    def has_add_permission(self, request):
        if self.is_admin(request):
            return True
        elif self.is_vendor(request):
            # Vendors can create their profile if they don't have one
            return not VendorProfile.objects.filter(user=request.user).exists()
        return False

    def make_approved(self, request, queryset):
        if not self.is_admin(request):
            raise PermissionDenied
        queryset.update(is_approved=True)
        self.message_user(request, "Selected vendors have been approved.")

    make_approved.short_description = "Mark selected vendors as approved"

    def make_not_approved(self, request, queryset):
        if not self.is_admin(request):
            raise PermissionDenied
        queryset.update(is_approved=False)
        self.message_user(request, "Selected vendors have been marked as not approved.")

    make_not_approved.short_description = "Mark selected vendors as not approved"


# Product-related Admin Classes (Vendor Access)
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductColorInline(admin.TabularInline):
    model = ProductColor
    extra = 1


class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin, UserTypePermissionMixin):
    list_display = [
        'name', 'category', 'subcategory', 'brand', 'price',
        'is_best_seller', 'is_new_arrival', 'is_on_sale',
        'is_active', 'created_at', 'get_vendor'
    ]
    list_filter = [
        'category', 'subcategory', 'brand', 'fit_type',
        'is_best_seller', 'is_new_arrival', 'is_on_sale',
        'is_featured', 'is_active', 'created_at'
    ]
    search_fields = ['name', 'description', 'brand__name']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ProductImageInline, ProductColorInline, ProductSizeInline, ProductVariantInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'short_description', 'vendor')
        }),
        ('Categorization', {
            'fields': ('category', 'subcategory', 'fit_type', 'brand')
        }),
        ('Pricing', {
            'fields': ('price', 'sale_price')
        }),
        ('Flags', {
            'fields': ('is_best_seller', 'is_new_arrival', 'is_on_sale', 'is_featured')
        }),
        ('Inventory', {
            'fields': ('stock_quantity', 'is_active', 'is_available')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Size Chart', {
            'fields': ('size_chart', 'delivery_return',),
            'classes': ('collapse',)
        }),
    )

    def get_vendor(self, obj):
        if hasattr(obj, 'vendor') and obj.vendor:
            return obj.vendor.store_name
        return "No vendor assigned"

    get_vendor.short_description = "Vendor"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self.is_admin(request):
            return qs
        elif self.is_vendor(request):
            # Vendors can only see their own products
            try:
                vendor_profile = VendorProfile.objects.get(user=request.user)
                return qs.filter(vendor=vendor_profile)
            except VendorProfile.DoesNotExist:
                return qs.none()
        else:
            # Customers cannot manage products
            return qs.none()

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if self.is_vendor(request):
            # Auto-assign vendor for new products
            if 'vendor' in form.base_fields:
                try:
                    vendor_profile = VendorProfile.objects.get(user=request.user)
                    form.base_fields['vendor'].initial = vendor_profile
                    form.base_fields['vendor'].widget = admin.widgets.AdminHiddenInput()
                except VendorProfile.DoesNotExist:
                    pass
        return form

    def save_model(self, request, obj, form, change):
        if self.is_vendor(request) and not change:
            # Auto-assign vendor for new products
            try:
                vendor_profile = VendorProfile.objects.get(user=request.user)
                obj.vendor = vendor_profile
            except VendorProfile.DoesNotExist:
                pass
        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        if self.is_admin(request):
            return True
        elif self.is_vendor(request):
            if obj is None:
                return True
            try:
                vendor_profile = VendorProfile.objects.get(user=request.user)
                return obj.vendor == vendor_profile
            except VendorProfile.DoesNotExist:
                return False
        return False

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)

    def has_add_permission(self, request):
        if self.is_admin(request):
            return True
        elif self.is_vendor(request):
            # Check if vendor has an approved profile
            try:
                vendor_profile = VendorProfile.objects.get(user=request.user)
                return vendor_profile.is_approved
            except VendorProfile.DoesNotExist:
                return False
        return False


# Order-related Admin Classes (Customer Access)
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['get_total_price']
    fields = ['product_variant', 'quantity', 'price_at_purchase', 'get_total_price']
    can_delete = False

    def get_total_price(self, obj):
        quantity = obj.quantity if obj.quantity is not None else Decimal('0.00')
        price_at_purchase = obj.price_at_purchase if obj.price_at_purchase is not None else Decimal('0.00')
        return quantity * price_at_purchase

    get_total_price.short_description = "Item Total"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin, UserTypePermissionMixin):
    list_display = [
        'order_number', 'user', 'full_name', 'grand_total',
        'status', 'payment_status', 'created_at', 'view_shipping_address', 'view_payment_info'
    ]
    list_filter = ['status', 'payment_status', 'created_at', 'updated_at']
    search_fields = ['order_number', 'user__username', 'full_name', 'email', 'phone_number']
    readonly_fields = [
        'order_number', 'created_at', 'updated_at',
        'subtotal', 'shipping_cost', 'grand_total', 'stripe_pid',
        'display_shipping_address', 'display_payment_info'
    ]
    inlines = [OrderItemInline]

    fieldsets = (
        ('Order Details', {
            'fields': ('order_number', 'user', 'status', 'payment_status', 'stripe_pid')
        }),
        ('Customer Information', {
            'fields': ('full_name', 'email', 'phone_number')
        }),
        ('Shipping Information', {
            'fields': ('display_shipping_address',),
            'classes': ('collapse',),
            'description': _("Details of the shipping address for this order.")
        }),
        ('Payment Information', {
            'fields': ('display_payment_info',),
            'classes': ('collapse',),
            'description': _("Details of the payment for this order.")
        }),
        ('Financials', {
            'fields': ('subtotal', 'shipping_cost', 'grand_total')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self.is_admin(request):
            return qs
        elif self.is_customer(request):
            # Customers can only see their own orders
            return qs.filter(user=request.user)
        elif self.is_vendor(request):
            # Vendors can see orders containing their products
            try:
                vendor_profile = VendorProfile.objects.get(user=request.user)
                return qs.filter(orderitem__product_variant__product__vendor=vendor_profile).distinct()
            except VendorProfile.DoesNotExist:
                return qs.none()
        return qs.none()

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        if not self.is_admin(request):
            # Non-admin users cannot edit most fields
            readonly_fields.extend(['user', 'full_name', 'email', 'phone_number'])
            if self.is_customer(request):
                readonly_fields.extend(['status', 'payment_status'])
        return readonly_fields

    def has_change_permission(self, request, obj=None):
        if self.is_admin(request):
            return True
        elif self.is_customer(request):
            return obj is None or obj.user == request.user
        elif self.is_vendor(request):
            if obj is None:
                return True
            try:
                vendor_profile = VendorProfile.objects.get(user=request.user)
                return obj.orderitem_set.filter(product_variant__product__vendor=vendor_profile).exists()
            except VendorProfile.DoesNotExist:
                return False
        return False

    def has_delete_permission(self, request, obj=None):
        # Only admins can delete orders
        return self.is_admin(request)

    def has_add_permission(self, request):
        # Orders are typically created through the frontend, not admin
        return self.is_admin(request)

    # Display methods (same as original)
    def display_shipping_address(self, obj):
        try:
            shipping_address = obj.shipping_address
            return format_html(
                "<strong>Full Name:</strong> {}<br>"
                "<strong>Address Line 1:</strong> {}<br>"
                "<strong>Address Line 2:</strong> {}<br>"
                "<strong>City:</strong> {}<br>"
                "<strong>State/Province:</strong> {}<br>"
                "<strong>Postal Code:</strong> {}<br>"
                "<strong>Country:</strong> {}<br>"
                "<strong>Phone Number:</strong> {}",
                shipping_address.full_name,
                shipping_address.address_line1,
                shipping_address.address_line2 if shipping_address.address_line2 else _("N/A"),
                shipping_address.city,
                shipping_address.state_province if shipping_address.state_province else _("N/A"),
                shipping_address.postal_code if shipping_address.postal_code else _("N/A"),
                shipping_address.country,
                shipping_address.phone_number
            )
        except ShippingAddress.DoesNotExist:
            return _("No shipping address associated with this order.")

    display_shipping_address.short_description = _("Shipping Address")

    def display_payment_info(self, obj):
        try:
            payment = obj.payment
            return format_html(
                "<strong>Transaction ID:</strong> {}<br>"
                "<strong>Payment Method:</strong> {}<br>"
                "<strong>Amount:</strong> {}<br>"
                "<strong>Success:</strong> {}<br>"
                "<strong>Timestamp:</strong> {}",
                payment.transaction_id,
                payment.payment_method,
                payment.amount,
                _("Yes") if payment.is_success else _("No"),
                payment.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            )
        except Payment.DoesNotExist:
            return _("No payment information associated with this order.")

    display_payment_info.short_description = _("Payment Information")

    def view_shipping_address(self, obj):
        try:
            shipping_address = obj.shipping_address
            url = reverse('admin:%s_%s_change' % (shipping_address._meta.app_label, shipping_address._meta.model_name),
                          args=[shipping_address.pk])
            return format_html('<a href="{}">{}</a>', url, _("View Shipping Address"))
        except ShippingAddress.DoesNotExist:
            return _("N/A")

    view_shipping_address.short_description = _("Shipping Address Link")
    view_shipping_address.allow_tags = True

    def view_payment_info(self, obj):
        try:
            payment = obj.payment
            url = reverse('admin:%s_%s_change' % (payment._meta.app_label, payment._meta.model_name),
                          args=[payment.pk])
            return format_html('<a href="{}">{}</a>', url, _("View Payment Info"))
        except Payment.DoesNotExist:
            return _("N/A")

    view_payment_info.short_description = _("Payment Info Link")
    view_payment_info.allow_tags = True


# Cart and Wishlist Admin (Customer Access)
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin, UserTypePermissionMixin):
    list_display = ['id', 'user_or_session', 'total_items', 'total_price', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'session_key']

    def user_or_session(self, obj):
        return obj.user.username if obj.user else f"Session: {obj.session_key}"

    user_or_session.short_description = 'Owner'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self.is_admin(request):
            return qs
        elif self.is_customer(request):
            return qs.filter(user=request.user)
        return qs.none()

    def has_change_permission(self, request, obj=None):
        if self.is_admin(request):
            return True
        elif self.is_customer(request):
            return obj is None or obj.user == request.user
        return False


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin, UserTypePermissionMixin):
    list_display = ['cart', 'product_name', 'variant_color', 'variant_size', 'quantity', 'added_at']
    list_filter = ['added_at']
    search_fields = ['cart__user__username', 'product_variant__product__name']

    def product_name(self, obj):
        return obj.product_variant.product.name

    def variant_color(self, obj):
        return obj.product_variant.color.name

    def variant_size(self, obj):
        return obj.product_variant.size.name

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self.is_admin(request):
            return qs
        elif self.is_customer(request):
            return qs.filter(cart__user=request.user)
        return qs.none()


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin, UserTypePermissionMixin):
    list_display = ['id', 'user', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self.is_admin(request):
            return qs
        elif self.is_customer(request):
            return qs.filter(user=request.user)
        return qs.none()


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin, UserTypePermissionMixin):
    list_display = ['wishlist', 'product_name', 'added_at']
    list_filter = ['added_at']
    search_fields = ['wishlist__user__username', 'product__name']

    def product_name(self, obj):
        return obj.product.name

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self.is_admin(request):
            return qs
        elif self.is_customer(request):
            return qs.filter(wishlist__user=request.user)
        return qs.none()


# Admin-only models (Categories, Brands, etc.)
@admin.register(HomeSlider)
class HomeSliderAdmin(admin.ModelAdmin, UserTypePermissionMixin):
    list_display = ('heading', 'subheading', 'order', 'is_active', 'preview_image',)
    list_editable = ('order', 'is_active')
    search_fields = ('heading', 'subheading', 'alt_text')
    list_filter = ('is_active',)
    ordering = ('order',)

    def preview_image(self, obj):
        if obj.image_resized:
            return format_html('<img src="{}" width="140" height="65" style="object-fit: cover;" />',
                               obj.image_resized.url)
        return "-"

    preview_image.short_description = "Preview"

    def has_module_permission(self, request):
        return self.is_admin(request)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin, UserTypePermissionMixin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}

    def has_module_permission(self, request):
        return self.is_admin(request)


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin, UserTypePermissionMixin):
    list_display = ['name', 'category', 'slug', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}

    def has_module_permission(self, request):
        return self.is_admin(request)


@admin.register(FitType)
class FitTypeAdmin(admin.ModelAdmin, UserTypePermissionMixin):
    list_display = ['name', 'slug', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}

    def has_module_permission(self, request):
        return self.is_admin(request)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin, UserTypePermissionMixin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}

    def has_module_permission(self, request):
        return self.is_admin(request)


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin, UserTypePermissionMixin):
    list_display = ['name', 'hex_code', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'hex_code']

    def has_module_permission(self, request):
        return self.is_admin(request)


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin, UserTypePermissionMixin):
    list_display = ['name', 'size_type', 'order', 'is_active']
    list_filter = ['size_type', 'is_active']
    search_fields = ['name']
    ordering = ['size_type', 'order']

    def has_module_permission(self, request):
        return self.is_admin(request)


# Product-related models that vendors can access
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin, UserTypePermissionMixin):
    list_display = ['product', 'alt_text', 'is_main', 'order', 'color', 'created_at']
    list_filter = ['is_main', 'color', 'created_at']
    search_fields = ['product__name', 'alt_text']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self.is_admin(request):
            return qs
        elif self.is_vendor(request):
            try:
                vendor_profile = VendorProfile.objects.get(user=request.user)
                return qs.filter(product__vendor=vendor_profile)
            except VendorProfile.DoesNotExist:
                return qs.none()
        return qs.none()


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin, UserTypePermissionMixin):
    list_display = ['product', 'color', 'size', 'sku', 'stock_quantity', 'is_available']
    list_filter = ['color', 'size', 'is_available']
    search_fields = ['product__name', 'sku']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self.is_admin(request):
            return qs
        elif self.is_vendor(request):
            try:
                vendor_profile = VendorProfile.objects.get(user=request.user)
                return qs.filter(product__vendor=vendor_profile)
            except VendorProfile.DoesNotExist:
                return qs.none()
        return qs.none()


# Read-only models for customers and vendors
@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin, UserTypePermissionMixin):
    list_display = ['user_display', 'full_name', 'address_line1', 'city', 'phone_number', 'is_default']
    list_filter = ['city', 'is_default']
    search_fields = ['user__username', 'full_name', 'address_line1', 'city', 'phone_number']

    readonly_fields = [
        'user', 'full_name', 'address_line1', 'address_line2', 'city',
        'phone_number', 'is_default'
    ]

    def user_display(self, obj):
        return obj.user.username if obj.user else _("N/A")

    user_display.short_description = _("User")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self.is_admin(request):
            return qs
        elif self.is_customer(request):
            return qs.filter(user=request.user)
        return qs.none()

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin, UserTypePermissionMixin):
    list_display = ['order', 'transaction_id', 'payment_method', 'amount', 'is_success', 'timestamp']
    list_filter = ['payment_method', 'is_success', 'timestamp']
    search_fields = ['order__order_number', 'transaction_id']

    readonly_fields = [
        'order', 'transaction_id', 'payment_method', 'amount',
        'is_success', 'timestamp', 'payment_details'
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self.is_admin(request):
            return qs
        elif self.is_customer(request):
            return qs.filter(order__user=request.user)
        elif self.is_vendor(request):
            try:
                vendor_profile = VendorProfile.objects.get(user=request.user)
                return qs.filter(order__orderitem__product_variant__product__vendor=vendor_profile).distinct()
            except VendorProfile.DoesNotExist:
                return qs.none()
        return qs.none()

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# Custom Dashboard Views
class CustomAdminConfig:
    """
    Configuration class to customize admin dashboard based on user type
    """

    @staticmethod
    def get_app_list(request, app_list):
        """
        Customize the app list based on user type
        """
        user_type = getattr(request.user, 'user_type', 'admin')

        if request.user.is_superuser or request.user.is_staff:
            # Admin sees everything - return original app_list
            return app_list

        # Filter apps and models based on user type
        filtered_app_list = []

        for app in app_list:
            if app['app_label'] == 'shop':
                filtered_models = []

                if user_type == 'vendor':
                    # Vendors can see: Products, ProductImages, ProductVariants, VendorProfile, Orders (their products)
                    allowed_models = [
                        'product', 'productimage', 'productvariant', 'vendorprofile', 'order', 'payment'
                    ]
                    for model in app['models']:
                        if model['object_name'].lower() in allowed_models:
                            filtered_models.append(model)

                elif user_type in ['customer', 'client']:
                    # Customers can see: Orders, Cart, CartItem, Wishlist, WishlistItem, ShippingAddress, Payment, User Profile
                    allowed_models = [
                        'order', 'cart', 'cartitem', 'wishlist', 'wishlistitem',
                        'shippingaddress', 'payment', 'mnoryuser'
                    ]
                    for model in app['models']:
                        if model['object_name'].lower() in allowed_models:
                            filtered_models.append(model)

                if filtered_models:
                    app['models'] = filtered_models
                    filtered_app_list.append(app)

            elif app['app_label'] == 'auth' and user_type in ['vendor', 'customer', 'client']:
                # Allow access to user management for profile editing
                filtered_models = []
                for model in app['models']:
                    if model['object_name'].lower() in ['user', 'mnoryuser']:
                        filtered_models.append(model)
                if filtered_models:
                    app['models'] = filtered_models
                    filtered_app_list.append(app)

        return filtered_app_list


# Monkey patch the admin site to use custom app list
original_get_app_list = admin.AdminSite.get_app_list


def custom_get_app_list(self, request):
    app_list = original_get_app_list(self, request)
    return CustomAdminConfig.get_app_list(request, app_list)


admin.AdminSite.get_app_list = custom_get_app_list


# Additional configuration for different user types
def admin_view_wrapper(view_func):
    """
    Decorator to add custom context to admin views
    """

    def wrapper(request, *args, **kwargs):
        # Add user type context
        request.user_type = getattr(request.user, 'user_type', 'admin')
        request.is_vendor = request.user_type == 'vendor'
        request.is_customer = request.user_type in ['customer', 'client']
        request.is_admin = request.user.is_superuser or request.user.is_staff

        return view_func(request, *args, **kwargs)

    return wrapper


# Custom index view
@admin_view_wrapper
def custom_admin_index(request, extra_context=None):
    """
    Custom admin index view with user-type specific content
    """
    extra_context = extra_context or {}

    if hasattr(request, 'is_vendor') and request.is_vendor:
        try:
            vendor_profile = VendorProfile.objects.get(user=request.user)
            extra_context['vendor_stats'] = {
                'store_name': vendor_profile.store_name,
                'product_count': vendor_profile.product_count,
                'wallet_balance': vendor_profile.wallet_balance,
                'is_approved': vendor_profile.is_approved,
            }
        except VendorProfile.DoesNotExist:
            extra_context['vendor_stats'] = {
                'needs_profile': True
            }

    elif hasattr(request, 'is_customer') and request.is_customer:
        # Customer stats
        orders = Order.objects.filter(user=request.user)
        extra_context['customer_stats'] = {
            'total_orders': orders.count(),
            'recent_orders': orders.order_by('-created_at')[:5],
            'wishlist_items': WishlistItem.objects.filter(wishlist__user=request.user).count(),
        }

    return admin.site.index(request, extra_context=extra_context)


# Override admin site index
admin.site.index = custom_admin_index

# Custom admin site configuration
admin.site.site_header = "Mnory Shop Administration"
admin.site.site_title = "Mnory Admin"
admin.site.index_title = "Welcome to Mnory Administration"


# Add custom CSS for different user types
def admin_media(request):
    """
    Add custom CSS based on user type
    """
    user_type = getattr(request.user, 'user_type', 'admin')
    css_files = ['admin/css/base.css']

    if user_type == 'vendor':
        css_files.append('admin/css/vendor.css')
    elif user_type in ['customer', 'client']:
        css_files.append('admin/css/customer.css')

    return {'css_files': css_files}


# Template tags for user type detection in templates
from django import template

register = template.Library()


@register.simple_tag
def user_type(user):
    return getattr(user, 'user_type', 'admin')


@register.simple_tag
def is_vendor(user):
    return getattr(user, 'user_type', 'admin') == 'vendor'


@register.simple_tag
def is_customer(user):
    return getattr(user, 'user_type', 'admin') in ['customer', 'client']


@register.simple_tag
def is_admin_user(user):
    return user.is_superuser or user.is_staff


# Custom permissions for model-level access
class CustomPermissionMixin:
    """
    Mixin to handle custom permissions based on user type
    """

    def has_view_permission(self, request, obj=None):
        """
        Custom view permission logic
        """
        if request.user.is_superuser or request.user.is_staff:
            return True

        user_type = getattr(request.user, 'user_type', None)
        model_name = self.model.__name__.lower()

        # Define permission mapping
        permission_map = {
            'vendor': {
                'allowed_models': [
                    'product', 'productimage', 'productvariant', 'productcolor',
                    'productsize', 'vendorprofile', 'order', 'orderitem', 'payment'
                ],
                'own_data_only': ['product', 'productimage', 'productvariant', 'vendorprofile']
            },
            'customer': {
                'allowed_models': [
                    'order', 'orderitem', 'cart', 'cartitem', 'wishlist',
                    'wishlistitem', 'shippingaddress', 'payment', 'mnoryuser'
                ],
                'own_data_only': ['order', 'cart', 'wishlist', 'shippingaddress', 'mnoryuser']
            },
            'client': {
                'allowed_models': [
                    'order', 'orderitem', 'cart', 'cartitem', 'wishlist',
                    'wishlistitem', 'shippingaddress', 'payment', 'mnoryuser'
                ],
                'own_data_only': ['order', 'cart', 'wishlist', 'shippingaddress', 'mnoryuser']
            }
        }

        if user_type in permission_map:
            return model_name in permission_map[user_type]['allowed_models']

        return False


# Apply the custom permission mixin to all admin classes
for admin_class in [
    MnoryUserAdmin, VendorProfileAdmin, ProductAdmin, OrderAdmin,
    CartAdmin, CartItemAdmin, WishlistAdmin, WishlistItemAdmin,
    ProductImageAdmin, ProductVariantAdmin, ShippingAddressAdmin, PaymentAdmin
]:
    # Add the mixin to the class if not already present
    if CustomPermissionMixin not in admin_class.__bases__:
        admin_class.__bases__ = (CustomPermissionMixin,) + admin_class.__bases__