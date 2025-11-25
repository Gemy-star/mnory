# shop/admin.py - Django Admin Configuration for E-commerce Platform
from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import (
    MnoryUser,
    VendorProfile,
    Category,
    SubCategory,
    Brand,
    FitType,
    Color,
    Size,
    Product,
    Order,
    Cart,
    Wishlist,
    ShippingAddress,
    Payment,
    Advertisement,
    Coupon,
    Message,
    VendorOrder,
    VendorShipping,
    Payout,
    Review,
    Notification,
    ChatbotQuestion,
    HomeSlider,
)
from .mixins import (
    AdminVendorCustomerOnlyMixin,
    AdminOnlyMixin,
    VendorFilterMixin,
    CustomerFilterMixin,
    UserRestrictedMixin,
    CustomerReadOnlyMixin,
    VendorAutoAssignMixin,
)

User = get_user_model()

# -----------------------------
# Custom Admin Classes
# -----------------------------


@admin.register(MnoryUser)
class MnoryUserAdmin(AdminOnlyMixin, UserRestrictedMixin, admin.ModelAdmin):
    list_display = ("email", "user_type", "is_active", "is_staff", "date_joined")
    search_fields = ("email", "phone_number", "first_name", "last_name")
    list_filter = ("user_type", "is_active", "is_staff", "date_joined")
    readonly_fields = ("date_joined", "last_login")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "phone_number")}),
        ("User Type", {"fields": ("user_type",)}),
        (
            "Permissions",
            {
                "fields": ("is_active", "is_staff", "is_superuser"),
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "user_type"),
            },
        ),
    )


@admin.register(VendorProfile)
class VendorProfileAdmin(AdminVendorCustomerOnlyMixin, admin.ModelAdmin):
    list_display = (
        "user_email",
        "vendor_business_name",
        "vendor_is_verified",
        "vendor_created_at",
    )
    search_fields = ("user__email", "business_name", "business_description")
    # Only include filters for fields that exist in the model
    list_filter = ("is_default",) if hasattr(VendorProfile, "is_default") else ()
    readonly_fields = ()

    fieldsets = (
        (
            "Basic Info",
            {
                "fields": (
                    "user",
                    "business_name",
                    "business_description",
                    "business_logo",
                )
            },
        ),
        (
            "Contact Details",
            {"fields": ("business_phone", "business_email", "business_address")},
        ),
        (
            "Verification",
            {
                "fields": (
                    ("is_verified", "verification_documents")
                    if hasattr(VendorProfile, "is_verified")
                    else ("verification_documents",)
                )
            },
        ),
    )

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = "User Email"
    user_email.admin_order_field = "user__email"

    def vendor_business_name(self, obj):
        return getattr(obj, "business_name", "N/A")

    vendor_business_name.short_description = "Business Name"

    def vendor_is_verified(self, obj):
        return getattr(obj, "is_verified", False)

    vendor_is_verified.short_description = "Verified"
    vendor_is_verified.boolean = True

    def vendor_created_at(self, obj):
        return getattr(obj, "created_at", None)

    vendor_created_at.short_description = "Created"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_admin_type:
            return qs
        elif request.user.is_vendor_type:
            return qs.filter(user=request.user)
        return qs.none()

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if request.user.is_vendor_type:
            readonly_fields.extend(["user"])
            if hasattr(VendorProfile, "is_verified"):
                readonly_fields.append("is_verified")
        # Dynamically add timestamp fields if they exist
        if obj and hasattr(obj, "created_at"):
            readonly_fields.append("created_at")
        if obj and hasattr(obj, "updated_at"):
            readonly_fields.append("updated_at")
        return readonly_fields

    def get_list_filter(self, request):
        """Dynamically build list_filter based on available fields"""
        filters = []
        if hasattr(VendorProfile, "is_verified"):
            filters.append("is_verified")
        if hasattr(VendorProfile, "created_at"):
            filters.append("created_at")
        return tuple(filters)


@admin.register(Product)
class ProductAdmin(
    AdminVendorCustomerOnlyMixin,
    VendorFilterMixin,
    VendorAutoAssignMixin,
    admin.ModelAdmin,
):
    list_display = (
        "name",
        "vendor_name",
        "price",
        "stock_quantity",
        "is_active",
        "created_at",
    )
    search_fields = ("name", "description", "vendor__business_name", "sku")
    list_filter = ("is_active", "category", "created_at")
    readonly_fields = ("created_at", "updated_at")
    filter_horizontal = ("tags",) if hasattr(Product, "tags") else ()

    fieldsets = (
        ("Basic Info", {"fields": ("name", "description", "category", "vendor")}),
        ("Pricing & Stock", {"fields": ("price", "stock_quantity", "sku")}),
        ("Media & Status", {"fields": ("image", "is_active")}),
        (
            "SEO & Tags",
            {
                "fields": (
                    ("meta_description", "tags")
                    if hasattr(Product, "tags")
                    else ("meta_description",)
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def vendor_name(self, obj):
        return obj.vendor.business_name if obj.vendor else "No Vendor"

    vendor_name.short_description = "Vendor"
    vendor_name.admin_order_field = "vendor__business_name"

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if request.user.is_vendor_type:
            readonly_fields.append("vendor")
        elif request.user.is_customer_type:
            readonly_fields.extend(["vendor", "price", "stock_quantity", "is_active"])
        return readonly_fields

    actions = ["activate_products", "deactivate_products"]

    def activate_products(self, request, queryset):
        if request.user.is_vendor_type:
            queryset = queryset.filter(vendor__user=request.user)
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} products were activated.")

    activate_products.short_description = "Activate selected products"

    def deactivate_products(self, request, queryset):
        if request.user.is_vendor_type:
            queryset = queryset.filter(vendor__user=request.user)
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} products were deactivated.")

    deactivate_products.short_description = "Deactivate selected products"


@admin.register(Order)
class OrderAdmin(
    AdminVendorCustomerOnlyMixin,
    CustomerFilterMixin,
    CustomerReadOnlyMixin,
    admin.ModelAdmin,
):
    list_display = (
        "id",
        "user_email",
        "status",
        "payment_status",
        "order_total_amount",
        "created_at",
    )
    search_fields = ("id", "user__email", "user__first_name", "user__last_name")
    list_filter = ("status", "payment_status", "created_at")
    readonly_fields = ("created_at", "updated_at", "order_number")
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Order Info",
            {"fields": ("order_number", "user", "status", "payment_status")},
        ),
        (
            "Financial",
            {
                "fields": (
                    "total_amount",
                    "shipping_cost",
                    "tax_amount",
                    "discount_amount",
                )
            },
        ),
        ("Addresses", {"fields": ("shipping_address", "billing_address")}),
        ("Notes", {"fields": ("notes", "admin_notes"), "classes": ("collapse",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = "Customer Email"
    user_email.admin_order_field = "user__email"

    def order_total_amount(self, obj):
        return getattr(obj, "total_amount", 0)

    order_total_amount.short_description = "Total Amount"

    actions = ["mark_as_processing", "mark_as_shipped", "mark_as_delivered"]

    def mark_as_processing(self, request, queryset):
        if request.user.is_customer_type:
            return
        updated = queryset.update(status="processing")
        self.message_user(request, f"{updated} orders marked as processing.")

    mark_as_processing.short_description = "Mark as Processing"

    def mark_as_shipped(self, request, queryset):
        if request.user.is_customer_type:
            return
        updated = queryset.update(status="shipped")
        self.message_user(request, f"{updated} orders marked as shipped.")

    mark_as_shipped.short_description = "Mark as Shipped"

    def mark_as_delivered(self, request, queryset):
        if request.user.is_customer_type:
            return
        updated = queryset.update(status="delivered")
        self.message_user(request, f"{updated} orders marked as delivered.")

    mark_as_delivered.short_description = "Mark as Delivered"


@admin.register(Cart)
class CartAdmin(AdminVendorCustomerOnlyMixin, CustomerFilterMixin, admin.ModelAdmin):
    list_display = ("id", "user_email", "items_count", "created_at", "updated_at")
    search_fields = ("user__email", "user__first_name", "user__last_name")
    readonly_fields = ("created_at", "updated_at")

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = "Customer Email"
    user_email.admin_order_field = "user__email"

    def items_count(self, obj):
        return obj.items.count() if hasattr(obj, "items") else 0

    items_count.short_description = "Items Count"

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if request.user.is_customer_type:
            readonly_fields.append("user")
        return readonly_fields


@admin.register(Wishlist)
class WishlistAdmin(
    AdminVendorCustomerOnlyMixin, CustomerFilterMixin, admin.ModelAdmin
):
    list_display = ("id", "user_email", "items_count", "created_at")
    search_fields = ("user__email", "user__first_name", "user__last_name")
    readonly_fields = ("created_at", "updated_at")

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = "Customer Email"
    user_email.admin_order_field = "user__email"

    def items_count(self, obj):
        return obj.products.count() if hasattr(obj, "products") else 0

    items_count.short_description = "Items Count"

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if request.user.is_customer_type:
            readonly_fields.append("user")
        return readonly_fields


@admin.register(ShippingAddress)
class ShippingAddressAdmin(
    AdminVendorCustomerOnlyMixin, CustomerFilterMixin, admin.ModelAdmin
):
    list_display = (
        "user_email",
        "full_name",
        "shipping_address_line_1",
        "city",
        "shipping_country",
        "is_default",
    )
    search_fields = ("user__email", "full_name", "city", "country", "address_line_1")
    readonly_fields = ()

    fieldsets = (
        ("Contact Info", {"fields": ("user", "full_name", "phone_number")}),
        (
            "Address",
            {
                "fields": (
                    "address_line_1",
                    "address_line_2",
                    "city",
                    "state",
                    "postal_code",
                    "country",
                )
            },
        ),
        ("Settings", {"fields": ("is_default",)}),
    )

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = "Customer Email"
    user_email.admin_order_field = "user__email"

    def shipping_address_line_1(self, obj):
        return getattr(obj, "address_line_1", "N/A")

    shipping_address_line_1.short_description = "Address"

    def shipping_country(self, obj):
        return getattr(obj, "country", "N/A")

    shipping_country.short_description = "Country"

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if request.user.is_customer_type:
            readonly_fields.append("user")
        # Dynamically add timestamp fields if they exist
        if obj and hasattr(obj, "created_at"):
            readonly_fields.append("created_at")
        if obj and hasattr(obj, "updated_at"):
            readonly_fields.append("updated_at")
        return readonly_fields

    def get_list_filter(self, request):
        """Dynamically build list_filter based on available fields"""
        filters = ["is_default"]
        if hasattr(ShippingAddress, "country"):
            filters.insert(0, "country")
        if hasattr(ShippingAddress, "created_at"):
            filters.append("created_at")
        return tuple(filters)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "contract_title",
        "amount",
        "payment_status_display",
        "payment_type_display",
        "payment_created_at",
    )
    search_fields = ("contract__title", "transaction_id")
    readonly_fields = ("transaction_id",)

    fieldsets = (
        ("Payment Info", {"fields": ("contract", "amount", "payment_type", "status")}),
        (
            "Transaction",
            {"fields": ("transaction_id", "description", "due_date", "paid_date")},
        ),
    )

    def contract_title(self, obj):
        return (
            obj.contract.title if hasattr(obj, "contract") and obj.contract else "N/A"
        )

    contract_title.short_description = "Contract"
    contract_title.admin_order_field = "contract__title"

    def payment_status_display(self, obj):
        return getattr(obj, "status", "N/A")

    payment_status_display.short_description = "Status"

    def payment_type_display(self, obj):
        return getattr(obj, "payment_type", "N/A")

    payment_type_display.short_description = "Payment Type"

    def payment_created_at(self, obj):
        return getattr(obj, "created_at", None)

    payment_created_at.short_description = "Created"

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        # Dynamically add timestamp fields if they exist
        if obj and hasattr(obj, "created_at"):
            readonly_fields.append("created_at")
        if obj and hasattr(obj, "updated_at"):
            readonly_fields.append("updated_at")
        return readonly_fields

    def get_list_filter(self, request):
        """Dynamically build list_filter based on available fields"""
        filters = []
        if hasattr(Payment, "status"):
            filters.append("status")
        if hasattr(Payment, "payment_type"):
            filters.append("payment_type")
        if hasattr(Payment, "created_at"):
            filters.append("created_at")
        return tuple(filters)

    def get_date_hierarchy(self, request):
        """Only set date_hierarchy if created_at field exists"""
        if hasattr(Payment, "created_at"):
            return "created_at"
        return None

    # Override to use dynamic date_hierarchy
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only set date_hierarchy if the field exists
        if hasattr(Payment, "created_at"):
            self.date_hierarchy = "created_at"
        else:
            self.date_hierarchy = None


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    """
    Admin interface for Advertisement model.
    Allows management of ads with analytics and scheduling.
    """

    list_display = (
        "title",
        "placement",
        "category",
        "is_active",
        "display_order",
        "view_count",
        "click_count",
        "start_date",
        "end_date",
        "created_at",
    )

    list_filter = (
        "is_active",
        "placement",
        "category",
        "created_at",
        "start_date",
        "end_date",
    )

    search_fields = ("title", "title_ar", "description", "description_ar")

    readonly_fields = ("click_count", "view_count", "created_at", "updated_at")

    fieldsets = (
        (
            "Content",
            {
                "fields": (
                    "title",
                    "title_ar",
                    "description",
                    "description_ar",
                    "image",
                    "link_url",
                )
            },
        ),
        (
            "Placement & Display",
            {"fields": ("placement", "category", "display_order", "is_active")},
        ),
        (
            "Scheduling",
            {"fields": ("start_date", "end_date"), "classes": ("collapse",)},
        ),
        (
            "Analytics",
            {"fields": ("view_count", "click_count"), "classes": ("collapse",)},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    ordering = ["display_order", "-created_at"]
    list_per_page = 25

    def get_queryset(self, request):
        """Optimize queryset with select_related for category."""
        qs = super().get_queryset(request)
        return qs.select_related("category")


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    """
    Admin interface for the Coupon model.
    """

    list_display = (
        "code",
        "discount_type",
        "discount_value",
        "is_active",
        "valid_from",
        "valid_to",
        "times_used",
        "max_uses",
    )
    list_filter = ("is_active", "discount_type", "valid_from", "valid_to")
    search_fields = ("code",)
    readonly_fields = ("times_used",)

    fieldsets = (
        ("Coupon Details", {"fields": ("code", "discount_type", "discount_value")}),
        (
            "Validity & Rules",
            {
                "fields": (
                    "is_active",
                    "valid_from",
                    "valid_to",
                    "min_purchase_amount",
                    "max_uses",
                    "max_uses_per_user",
                )
            },
        ),
        ("Usage Stats", {"fields": ("times_used",), "classes": ("collapse",)}),
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("order", "sender", "recipient", "created_at", "is_read")
    list_filter = ("is_read", "created_at")
    search_fields = ("order__order_number", "sender__email", "recipient__email", "body")
    readonly_fields = ("created_at",)


@admin.register(ChatbotQuestion)
class ChatbotQuestionAdmin(admin.ModelAdmin):
    list_display = ("short_question", "user", "language_code", "created_at")
    list_filter = ("language_code", "created_at")
    search_fields = ("question", "answer", "user__email")
    readonly_fields = (
        "user",
        "question",
        "answer",
        "language_code",
        "source_path",
        "created_at",
    )

    def short_question(self, obj):
        return (obj.question or "")[:80]

    short_question.short_description = "Question"


@admin.register(VendorOrder)
class VendorOrderAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "vendor",
        "subtotal",
        "shipping_charged",
        "commission_amount",
        "net_payout",
        "created_at",
    )
    list_filter = ("vendor", "created_at")
    search_fields = ("order__order_number", "vendor__store_name")
    readonly_fields = ("created_at", "net_payout")


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ("vendor", "amount", "status", "requested_at", "completed_at")
    list_filter = ("status", "requested_at", "completed_at")
    search_fields = ("vendor__store_name", "vendor__user__email")
    readonly_fields = ("requested_at", "completed_at")
    actions = ["mark_as_completed", "mark_as_failed"]

    def mark_as_completed(self, request, queryset):
        from django.utils import timezone

        for payout in queryset.filter(status="pending"):
            payout.status = "completed"
            payout.completed_at = timezone.now()
            payout.save()
        self.message_user(
            request,
            f"{queryset.filter(status='completed').count()} payouts marked as completed.",
        )

    mark_as_completed.short_description = "Mark selected payouts as Completed"

    def mark_as_failed(self, request, queryset):
        from django.db import transaction

        payouts_to_fail = queryset.filter(status="pending")
        failed_count = 0
        for payout in payouts_to_fail:
            with transaction.atomic():
                # Refund the amount to the vendor's wallet
                vendor = payout.vendor
                vendor.wallet_balance += payout.amount
                vendor.save(update_fields=["wallet_balance"])

                payout.status = "failed"
                payout.save()

                # Notify the vendor
                from shop.models import Notification
                from django.utils.translation import gettext as _

                Notification.objects.create(
                    user=vendor.user,
                    notification_type="general",
                    title=_("Payout Request Failed"),
                    message=_(
                        "Your payout request for {amount} EGP has failed and the amount has been returned to your wallet."
                    ).format(amount=payout.amount),
                    link=reverse("shop:vendor_dashboard"),
                )
                failed_count += 1

        if failed_count > 0:
            self.message_user(
                request,
                f"{failed_count} payouts marked as failed and amounts refunded to vendor wallets.",
            )

    mark_as_failed.short_description = "Mark selected payouts as Failed (and refund)"


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ("name", "hex_code", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ("name", "size_type", "order", "is_active")
    list_filter = ("size_type", "is_active")
    search_fields = ("name",)
    ordering = ("size_type", "order", "name")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at")
    search_fields = ("name", "slug")
    list_filter = ("is_active", "created_at")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "slug", "is_active", "created_at")
    search_fields = ("name", "slug", "category__name")
    list_filter = ("category", "is_active", "created_at")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    search_fields = ("name", "slug")
    list_filter = ("is_active",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(FitType)
class FitTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    search_fields = ("name", "slug")
    list_filter = ("is_active",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(HomeSlider)
class HomeSliderAdmin(admin.ModelAdmin):
    list_display = ("heading", "order", "is_active")
    search_fields = ("heading", "subheading")
    list_filter = ("is_active",)
    ordering = ("order",)


@admin.register(VendorShipping)
class VendorShippingAdmin(admin.ModelAdmin):
    list_display = (
        "vendor",
        "shipping_rate_cairo",
        "shipping_rate_outside_cairo",
        "free_shipping_threshold",
    )
    search_fields = ("vendor__store_name", "vendor__user__email")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "is_public", "created_at")
    search_fields = ("product__name", "user__email", "comment")
    list_filter = ("is_public", "rating", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "notification_type", "title", "is_read", "created_at")
    search_fields = ("user__email", "title", "message")
    list_filter = ("notification_type", "is_read", "created_at")
    readonly_fields = ("created_at",)
