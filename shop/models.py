# shop/models.py

from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from django.conf import settings  # Import settings to get AUTH_USER_MODEL
from django.db.models import Avg
from django.contrib.auth.models import AbstractUser
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from django.utils.translation import gettext_lazy as _
from colorfield.fields import ColorField
import uuid
from constance import config
from django_ckeditor_5.fields import CKEditor5Field


class MnoryUser(AbstractUser):
    # Define choices for user types
    USER_TYPE_CHOICES = (
        ("admin", "Admin"),
        ("vendor", "Vendor"),
        ("customer", "Customer"),
        ("company", "Company"),
        ("freelancer", "Freelancer"),
        ("affiliate", "Affiliate"),
    )

    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        blank=True,  # Allow blank
        null=True,  # Allow null
        help_text=_(
            "Optional. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )

    email = models.EmailField(_("email address"), unique=True)  # Main identifier

    phone_number = models.CharField(
        max_length=15,
        unique=True,
        blank=True,
        null=True,
        help_text="User's phone number, must be unique if provided.",
    )

    # Main field for user role/type
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default="customer",
        help_text="Defines the primary role or type of the user.",
    )

    # Set email as the USERNAME_FIELD for authentication
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # No extra required fields

    class Meta:
        verbose_name = "Mnory User"
        verbose_name_plural = "Mnory Users"

    def __str__(self):
        return f"{self.email} ({self.get_user_type_display()})"

    # --- Helper methods (renamed to avoid conflict with Django internals) ---
    @property
    def is_admin_type(self):
        return self.user_type == "admin"

    @property
    def is_vendor_type(self):
        return self.user_type == "vendor"

    @property
    def is_customer_type(self):
        return self.user_type == "customer"

    @property
    def is_company_type(self):
        return self.user_type == "company"

    @property
    def is_freelancer_type(self):
        return self.user_type == "freelancer"

    @property
    def is_affiliate_type(self):
        return self.user_type == "affiliate"

    # Aliases for freelancing app compatibility
    @property
    def is_freelancer_user(self):
        return self.user_type == "freelancer"

    @property
    def is_company_user(self):
        return self.user_type == "company"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image_resized = ImageSpecField(
        source="image",
        processors=[ResizeToFill(376, 477)],
        format="JPEG",
        options={"quality": 85},
    )

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("shop:category_detail", kwargs={"slug": self.slug})


class SubCategory(models.Model):
    category = models.ForeignKey(
        Category, related_name="subcategories", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="subcategories/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image_resized = ImageSpecField(
        source="image",
        processors=[ResizeToFill(376, 477)],
        format="JPEG",
        options={"quality": 85},
    )

    class Meta:
        verbose_name_plural = "Sub Categories"
        unique_together = ["category", "slug"]
        ordering = ["name"]

    def __str__(self):
        return f"{self.category.name} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(
            "shop:subcategory_detail",
            kwargs={"category_slug": self.category.slug, "slug": self.slug},
        )


class FitType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    logo = models.ImageField(upload_to="brands/", blank=True, null=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    logo_resized = ImageSpecField(
        source="logo",
        processors=[ResizeToFill(376, 477)],
        format="JPEG",
        options={"quality": 85},
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Color(models.Model):
    name = models.CharField(max_length=50, unique=True)
    hex_code = ColorField(
        default="#FFFFFF",
        verbose_name=_("Color Code"),
        help_text="Color hex code (e.g., #FF0000)",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Size(models.Model):
    SIZE_TYPES = [
        ("clothing", "Clothing"),
        ("shoes", "Shoes"),
        ("accessories", "Accessories"),
    ]

    name = models.CharField(max_length=20)
    size_type = models.CharField(max_length=20, choices=SIZE_TYPES, default="clothing")
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["size_type", "order", "name"]
        unique_together = ["name", "size_type"]

    def __str__(self):
        return f"{self.name} ({self.get_size_type_display()})"  # type: ignore


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True)

    category = models.ForeignKey(
        "Category", related_name="products", on_delete=models.CASCADE
    )  # Use string if not imported
    subcategory = models.ForeignKey(
        "SubCategory", related_name="products", on_delete=models.CASCADE
    )  # Use string if not imported
    fit_type = models.ForeignKey(
        "FitType",
        related_name="products",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )  # Use string if not imported
    brand = models.ForeignKey(
        "Brand",
        related_name="products",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )  # Use string if not imported
    vendor = models.ForeignKey(
        "VendorProfile",
        related_name="products",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )  # Use string if not imported

    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    sale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    # Flags
    is_best_seller = models.BooleanField(default=False)
    is_new_arrival = models.BooleanField(default=False)
    is_on_sale = models.BooleanField(default=False)  # Will be auto-set in save()
    is_featured = models.BooleanField(default=False)

    # Stock status
    stock_quantity = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )  # This might become less relevant with variants
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)

    # SEO fields
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)

    # Aggregated review fields
    average_rating = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.00, editable=False
    )
    review_count = models.PositiveIntegerField(default=0, editable=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Many-to-many (through ProductColor/ProductSize/ProductVariant)
    colors = models.ManyToManyField(Color, through="ProductColor", blank=True)
    sizes = models.ManyToManyField(Size, through="ProductSize", blank=True)
    size_chart = CKEditor5Field(
        blank=True, null=True, help_text="Add size chart content here (HTML supported)"
    )
    delivery_return = CKEditor5Field(
        blank=True,
        null=True,
        help_text="Add Delivery and return policy (HTML supported)",
    )

    @property
    def price_egp(self):
        """
        Calculates the price in EGP based on the USD price and the
        exchange rate from settings.
        """
        # Get the current price (sale price if applicable)
        current_usd_price = (
            self.sale_price if self.is_on_sale and self.sale_price else self.price
        )

        # Access the exchange rate from settings
        rate = Decimal(str(config.EXCHANGE_RATE_USD_TO_EGP))

        # Return the calculated EGP price
        return current_usd_price * rate

    @property
    def price_usd(self):
        """
        return price in USD
        """
        # Get the current price (sale price if applicable)
        current_usd_price = (
            self.sale_price if self.is_on_sale and self.sale_price else self.price
        )

        # Return the calculated USD price
        return current_usd_price

    @property
    def price_egp_no_sale(self):
        """
        Calculates the price in EGP based on the USD price and the
        exchange rate from settings.
        """
        current_usd_price = self.price

        # Access the exchange rate from settings
        rate = Decimal(str(config.EXCHANGE_RATE_USD_TO_EGP))

        # Return the calculated EGP price
        return current_usd_price * rate

    @property
    def price_usd_no_sale(self):
        """
        return price in USD
        """
        # Get the current price (sale price if applicable)
        current_usd_price = self.price

        # Return the calculated USD price
        return current_usd_price

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["category", "subcategory"]),
            models.Index(fields=["is_active", "is_available"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        # Automatically set is_on_sale
        if self.sale_price and self.sale_price < self.price:
            self.is_on_sale = True
        else:
            self.is_on_sale = False

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("shop:product_detail", kwargs={"slug": self.slug})

    @property
    def get_price(self):
        """Return current price (sale price if applicable)"""
        if self.is_on_sale and self.sale_price:
            return self.sale_price
        return self.price

    @property
    def get_discount_percentage(self):
        """Return discount percentage if on sale"""
        if self.is_on_sale and self.sale_price:
            discount = (self.price - self.sale_price) / self.price
            return round(discount * 100)
        return 0

    @property
    def is_in_stock(self):
        """Return if total stock is above 0 from any variant"""
        return self.variants.filter(stock_quantity__gt=0, is_available=True).exists()

    def get_main_image(self):
        """Return the main image or fallback to first image"""
        main_image = self.images.filter(is_main=True).first()
        return main_image or self.images.first()

    def get_hover_image(self):
        """Return the hover image or fallback to first image"""
        hover_image = self.images.filter(is_hover=True).first()
        return hover_image or self.images.first()

    def get_available_colors(self):
        """Return distinct active colors that have at least one variant in stock."""
        return Color.objects.filter(
            is_active=True,
            productvariant__product=self,
            productvariant__stock_quantity__gt=0,
            productvariant__is_available=True,
        ).distinct()

    def get_available_sizes(self, color_id=None):
        """
        Return distinct active sizes that have at least one variant in stock.
        Optionally filter by a specific color.
        """
        filters = (
            Q(is_active=True)
            & Q(productvariant__product=self)
            & Q(productvariant__stock_quantity__gt=0)
            & Q(productvariant__is_available=True)
        )

        if color_id:
            filters &= Q(productvariant__color_id=color_id)

        return (
            Size.objects.filter(filters)
            .distinct()
            .order_by("size_type", "order", "name")
        )

    @property
    def get_all_product_sizes_by_type(self):
        """
        Return all active sizes that match the product's category's size_type.
        Assumes Category model has a size_type field or you derive it.
        For simplicity here, let's assume `self.category.size_type` exists.
        If not, you'd need to explicitly set `size_type` on the Product or deduce it.
        """
        if hasattr(self.category, "size_type") and self.category.size_type:
            return Size.objects.filter(
                is_active=True, size_type=self.category.size_type
            ).order_by("size_type", "order", "name")
        else:
            return Size.objects.filter(is_active=True).order_by(
                "size_type", "order", "name"
            )

    def update_review_stats(self):
        """Recalculates and saves the average rating and review count."""
        reviews = self.reviews.filter(is_public=True)
        self.average_rating = reviews.aggregate(Avg("rating"))["rating__avg"] or 0
        self.review_count = reviews.count()
        self.save(update_fields=["average_rating", "review_count"])


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, related_name="images", on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=200, blank=True)
    is_main = models.BooleanField(default=False)
    is_hover = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    color = models.ForeignKey(
        Color,
        related_name="product_images",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    image_resized = ImageSpecField(
        source="image",
        processors=[ResizeToFill(376, 477)],
        format="JPEG",
        options={"quality": 85},
    )
    thumb_resized = ImageSpecField(
        source="image",
        processors=[ResizeToFill(709, 920)],
        format="JPEG",
        options={"quality": 70},
    )

    class Meta:
        ordering = ["order", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "color"],
                condition=Q(is_main=True),
                name="unique_main_image_per_product_color",
            ),
            models.UniqueConstraint(
                fields=["product", "color"],
                condition=Q(is_hover=True),
                name="unique_hover_image_per_product_color",
            ),
        ]

    def __str__(self):
        return f"{self.product.name} - Image {self.order}"

    def save(self, *args, **kwargs):
        if self.is_main:
            # Ensure only one main image per product and color
            ProductImage.objects.filter(
                product=self.product, color=self.color, is_main=True
            ).exclude(pk=self.pk).update(is_main=False)
        if self.is_hover:
            # Ensure only one hover image per product and color
            ProductImage.objects.filter(
                product=self.product, color=self.color, is_hover=True
            ).exclude(pk=self.pk).update(is_hover=False)
        super().save(*args, **kwargs)


class ProductColor(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    color = models.ForeignKey(Color, on_delete=models.CASCADE)
    stock_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["product", "color"]

    def __str__(self):
        return f"{self.product.name} - {self.color.name}"


class ProductSize(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    stock_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["product", "size"]

    def __str__(self):
        return f"{self.product.name} - {self.size.name}"


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product, related_name="variants", on_delete=models.CASCADE
    )
    color = models.ForeignKey(Color, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    sku = models.CharField(max_length=100, unique=True, blank=True)
    stock_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    price_adjustment = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["product", "color", "size"]

    def __str__(self):
        return f"{self.product.name} - {self.color.name} - {self.size.name}"

    @property
    def get_price(self):
        """Get the price for this variant"""
        base_price = self.product.get_price
        return base_price + self.price_adjustment

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = f"{self.product.slug}-{self.color.name.lower()}-{self.size.name.lower()}".replace(
                " ", "-"
            )
        super().save(*args, **kwargs)


# --- Cart Models ---
class Cart(models.Model):
    session_key = models.CharField(
        max_length=40, null=True, blank=True, unique=True
    )  # For anonymous users
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.OneToOneField(
        MnoryUser, on_delete=models.CASCADE, null=True, blank=True, related_name="cart"
    )

    total_items_field = models.PositiveIntegerField(default=0)
    total_price_field = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )

    class Meta:
        verbose_name = "Shopping Cart"
        verbose_name_plural = "Shopping Carts"

    def __str__(self):
        if self.user:
            return f"Cart of {self.user.username}"
        return f"Anonymous Cart ({self.session_key})"

    @property
    def total_items(self):
        return (
            self.items.aggregate(total_quantity=models.Sum("quantity"))[
                "total_quantity"
            ]
            or 0
        )

    @property
    def total_price(self):
        return sum(item.get_total_price() for item in self.items.all())

    def update_totals(self):
        total_quantity = (
            self.items.aggregate(total_quantity=models.Sum("quantity"))[
                "total_quantity"
            ]
            or 0
        )
        total_price = sum(item.get_total_price() for item in self.items.all())
        self.total_items_field = total_quantity
        self.total_price_field = total_price
        self.save()
        return total_quantity, total_price


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("cart", "product_variant")
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"

    def __str__(self):
        return f"{self.quantity} x {self.product_variant.product.name} ({self.product_variant.color.name}, {self.product_variant.size.name})"

    def get_total_price(self):
        price = (
            self.product_variant.get_price()
            if callable(getattr(self.product_variant, "get_price", None))
            else self.product_variant.get_price
        )
        return self.quantity * price


# --- Wishlist Models ---
class Wishlist(models.Model):
    user = models.OneToOneField(
        MnoryUser, on_delete=models.CASCADE, related_name="wishlist"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Wishlist"
        verbose_name_plural = "Wishlists"

    def __str__(self):
        return f"Wishlist of {self.user.username}"


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(
        Wishlist, related_name="items", on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE
    )  # Wishlist can be for a product, not necessarily a variant
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (
            "wishlist",
            "product",
        )  # A product can only be in a wishlist once
        verbose_name = "Wishlist Item"
        verbose_name_plural = "Wishlist Items"

    def __str__(self):
        return f"{self.product.name} in {self.wishlist.user.username}'s Wishlist"


class HomeSlider(models.Model):
    image = models.ImageField(upload_to="slider/", verbose_name=_("Slider Image"))
    # Processed image (1920x600)
    image_resized = ImageSpecField(
        source="image",
        processors=[ResizeToFill(1400, 650)],
        format="JPEG",
        options={"quality": 85},
    )

    alt_text = models.CharField(max_length=255, verbose_name=_("Alt Text"))
    heading = models.CharField(max_length=255, verbose_name=_("Heading"))
    subheading = models.TextField(verbose_name=_("Subheading"))
    button_text = models.CharField(max_length=100, verbose_name=_("Button Text"))
    button_url_name = models.URLField(
        max_length=100,
        verbose_name=_("URL Address"),
        help_text=_("Enter the URL Address"),
    )
    order = models.PositiveIntegerField(default=0, verbose_name=_("Display Order"))
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))

    class Meta:
        ordering = ["order"]
        verbose_name = _("Home Slider")
        verbose_name_plural = _("Home Sliders")

    def __str__(self):
        return self.heading


# --- Order Models ---


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    order_number = models.CharField(
        max_length=32, null=False, editable=False, unique=True
    )
    user = models.ForeignKey(
        MnoryUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )

    # Billing Information (can be same as shipping or separate)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    phone_number = models.CharField(max_length=20)

    # Order Totals
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    shipping_cost = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    grand_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default="pending"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Stripe Payment Intent ID (for processing payments)
    stripe_pid = models.CharField(max_length=255, null=True, blank=True)

    # Coupon related fields
    coupon = models.ForeignKey(
        "Coupon",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def _generate_order_number(self):
        """
        Generate a random, unique order number using UUID
        """
        return uuid.uuid4().hex.upper()

    def save(self, *args, **kwargs):
        """
        Override the original save method to set the order number
        if it hasn't been set already.
        """
        if not self.order_number:
            self.order_number = self._generate_order_number()
        super().save(*args, **kwargs)

    def update_total(self):
        """Recalculates the grand total."""
        self.grand_total = self.subtotal + self.shipping_cost - self.discount_amount
        self.save(update_fields=["grand_total"])

    def __str__(self):
        return self.order_number

    def get_absolute_url(self):
        return reverse("shop:order_detail", args=[self.order_number])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product_variant = models.ForeignKey(
        ProductVariant, on_delete=models.PROTECT
    )  # Protect from deletion if order exists
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price_at_purchase = models.DecimalField(
        max_digits=10, decimal_places=2
    )  # Price at the time of purchase

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self):
        return f"{self.quantity} x {self.product_variant.product.name} ({self.product_variant.color.name}, {self.product_variant.size.name}) in Order {self.order.order_number}"

    def get_total_price(self):
        return self.quantity * self.price_at_purchase


class ShippingAddress(models.Model):
    """Stores shipping address details, optionally linked to an order or user."""

    CITY_CHOICE = (
        ("OUTSIDE_CAIRO", _("Outside Cairo")),
        ("INSIDE_CAIRO", _("Inside Cairo")),
    )

    order = models.OneToOneField(
        "Order",  # Use string if Order is defined later or import it
        related_name="shipping_address",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Order"),
    )
    user = models.ForeignKey(
        "MnoryUser",  # Use string if MnoryUser is defined later or import it
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="shipping_addresses",
        verbose_name=_("User"),
    )
    full_name = models.CharField(max_length=255, verbose_name=_("Full Name"))
    email = models.EmailField(null=True, blank=True, verbose_name=_("Email"))
    address_line1 = models.TextField(verbose_name=_("Address Line 1"))
    address_line2 = models.CharField(
        max_length=255, blank=True, null=True, verbose_name=_("Address Line 2")
    )
    city = models.CharField(max_length=100, verbose_name=_("City"))
    phone_number = models.CharField(max_length=20, verbose_name=_("Phone Number"))
    is_default = models.BooleanField(
        default=False, verbose_name=_("Is Default Address")
    )

    class Meta:
        verbose_name = _("Shipping Address")
        verbose_name_plural = _("Shipping Addresses")
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(is_default=True),
                name="unique_default_address_per_user",
            )
        ]

    def __str__(self):
        return f"Shipping Address for {self.full_name}, {self.city}"

    def save(self, *args, **kwargs):
        if self.is_default and self.user:
            # Unset other default addresses for this user
            ShippingAddress.objects.filter(user=self.user, is_default=True).exclude(
                pk=self.pk
            ).update(is_default=False)
        super().save(*args, **kwargs)


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ("credit_card", "Credit Card"),
        ("paypal", "PayPal"),
        ("bank_transfer", "Bank Transfer"),
        ("cash_on_delivery", "Cash on Delivery"),
        # Add more as needed
    ]

    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="payment"
    )
    transaction_id = models.CharField(
        max_length=255, unique=True, blank=True, null=True
    )
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    is_success = models.BooleanField(default=False)

    # Store additional payment details (e.g., last 4 digits of card, PayPal email)
    payment_details = models.JSONField(blank=True, null=True)

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"Payment for Order {self.order.order_number} - {self.payment_method}"


class Review(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews"
    )
    user = models.ForeignKey(
        MnoryUser, on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    reply = models.TextField(blank=True, null=True, verbose_name=_("Vendor Reply"))
    replied_at = models.DateTimeField(null=True, blank=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("product", "user")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Review for {self.product.name} by {self.user.email}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.product.update_review_stats()


class VendorProfile(models.Model):
    """Vendor (Merchant) profile linked to User."""

    PROFILE_TYPE_CHOICES = [
        ("free", "Free"),
        ("premium", "Premium"),
    ]
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vendorprofile"
    )
    store_name = models.CharField(max_length=255, verbose_name="Store Name")
    store_description = models.TextField(
        null=True, blank=True, verbose_name="Store Description"
    )
    logo = models.ImageField(
        upload_to="vendor_logos/", null=True, blank=True, verbose_name="Store Logo"
    )
    website = models.URLField(null=True, blank=True, verbose_name="Store Website URL")
    product_count = models.PositiveIntegerField(
        default=0, verbose_name="Number of Products"
    )
    country_of_operation = models.CharField(
        max_length=200, null=True, blank=True, verbose_name="Country of Operation"
    )
    wallet_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Wallet Balance",
    )
    profile_type = models.CharField(
        max_length=10,
        choices=PROFILE_TYPE_CHOICES,
        default="free",
        verbose_name="Profile Type",
    )
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("10.00"),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_(
            "Commission percentage taken by the platform from this vendor's sales (e.g., 10 for 10%)."
        ),
    )
    is_approved = models.BooleanField(default=False)
    logo_resized = ImageSpecField(
        source="logo",
        processors=[ResizeToFill(1920, 600)],
        format="JPEG",
        options={"quality": 85},
    )
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    def __str__(self):
        return f"Vendor Profile for {self.user.email} with store {self.store_name}"

    @property
    def is_premium(self) -> bool:
        return self.profile_type == "premium"

    def update_product_count(self):
        """Update the count of products in the vendor's store."""
        self.product_count = (
            self.user.products.count()
        )  # Assuming related_name='products' on Product model
        self.save()

    def deposit(self, amount: Decimal):
        """Add funds to the wallet."""
        if amount > 0:
            self.wallet_balance += amount
            self.save()

    def withdraw(self, amount: Decimal) -> bool:
        """Withdraw funds from the wallet. Returns True if successful."""
        if 0 < amount <= self.wallet_balance:
            self.wallet_balance -= amount
            self.save()
            return True
        return False

    def upgrade_to_premium(self) -> bool:
        """Upgrade vendor to premium if they have enough balance."""
        if self.profile_type == "premium":
            return True  # Already premium
        if self.wallet_balance >= settings.PREMIUM_UPGRADE_FEE:
            self.wallet_balance -= settings.PREMIUM_UPGRADE_FEE
            self.profile_type = "premium"
            self.save()
            return True
        return False

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.store_name)
            # Ensure uniqueness in case slugify produces duplicates
            original_slug = self.slug
            counter = 1
            while VendorProfile.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("shop:vendor_detail", kwargs={"slug": self.slug})


class VendorOrder(models.Model):
    """
    Represents a vendor's portion of a customer's multi-vendor order.
    This model stores the financial breakdown for each vendor in an order.
    """

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="vendor_orders"
    )
    vendor = models.ForeignKey(
        VendorProfile, on_delete=models.PROTECT, related_name="vendor_orders"
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("Subtotal of vendor's items in this order."),
    )
    shipping_charged = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("Shipping cost charged for this vendor's items."),
    )
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text=_("Commission rate at the time of order (%)."),
    )
    commission_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("Commission amount taken by the platform."),
    )
    net_payout = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("The final amount to be paid out to the vendor."),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("order", "vendor")
        ordering = ["-created_at"]
        verbose_name = _("Vendor Order")
        verbose_name_plural = _("Vendor Orders")

    def __str__(self):
        return f"{self.vendor.store_name}'s part of Order #{self.order.order_number}"

    def save(self, *args, **kwargs):
        self.net_payout = self.subtotal + self.shipping_charged - self.commission_amount
        super().save(*args, **kwargs)


class VendorShipping(models.Model):
    """Model to store vendor-specific shipping settings."""

    vendor = models.OneToOneField(
        VendorProfile, on_delete=models.CASCADE, related_name="shipping_settings"
    )
    shipping_rate_cairo = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("60.00")
    )
    shipping_rate_outside_cairo = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("100.00")
    )
    free_shipping_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_(
            "Offer free shipping for orders from this vendor above this amount. Leave blank to disable."
        ),
    )

    class Meta:
        verbose_name = _("Vendor Shipping Setting")
        verbose_name_plural = _("Vendor Shipping Settings")

    def __str__(self):
        return f"Shipping settings for {self.vendor.store_name}"


class Payout(models.Model):
    """Model to track vendor payout requests."""

    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("completed", _("Completed")),
        ("failed", _("Failed")),
    ]

    vendor = models.ForeignKey(
        VendorProfile, on_delete=models.CASCADE, related_name="payouts"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    transaction_details = models.TextField(
        blank=True, help_text=_("e.g., Bank Transaction ID, confirmation number.")
    )

    class Meta:
        ordering = ["-requested_at"]

    def __str__(self):
        return f"Payout of {self.amount} for {self.vendor.store_name} on {self.requested_at.date()}"


class Advertisement(models.Model):
    """
    Advertisement model for displaying ads on home page, category pages, etc.
    Supports GIF and static images with scheduling and analytics.
    """

    PLACEMENT_CHOICES = [
        ("home", "Home Page"),
        ("category", "Category Page"),
        ("product", "Product Page"),
        ("all", "All Pages"),
    ]

    title = models.CharField(max_length=255, verbose_name=_("Title"))
    title_ar = models.CharField(
        max_length=255, blank=True, verbose_name=_("Title (Arabic)")
    )
    description = models.TextField(blank=True, verbose_name=_("Description"))
    description_ar = models.TextField(
        blank=True, verbose_name=_("Description (Arabic)")
    )

    image = models.ImageField(
        upload_to="ads/",
        verbose_name=_("Advertisement Image"),
        help_text=_("Supports GIF and static images. Recommended size: 1200x500px"),
    )

    link_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name=_("Link URL"),
        help_text=_("URL to redirect when ad is clicked"),
    )

    placement = models.CharField(
        max_length=20,
        choices=PLACEMENT_CHOICES,
        default="home",
        verbose_name=_("Placement"),
        help_text=_("Where this ad should be displayed"),
    )

    category = models.ForeignKey(
        "Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="advertisements",
        verbose_name=_("Category"),
        help_text=_("Optional: Show this ad only on specific category page"),
    )

    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    display_order = models.IntegerField(
        default=0,
        verbose_name=_("Display Order"),
        help_text=_("Lower numbers appear first"),
    )

    # Scheduling
    start_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Start Date"),
        help_text=_("Optional: When to start showing this ad"),
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("End Date"),
        help_text=_("Optional: When to stop showing this ad"),
    )

    # Analytics
    click_count = models.IntegerField(default=0, verbose_name=_("Click Count"))
    view_count = models.IntegerField(default=0, verbose_name=_("View Count"))

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        ordering = ["display_order", "-created_at"]
        verbose_name = _("Advertisement")
        verbose_name_plural = _("Advertisements")

    def __str__(self):
        return self.title

    @classmethod
    def get_active_ads(cls, placement=None, category=None):
        """
        Get active advertisements based on placement and category.
        Filters by date range if specified.
        """
        from django.utils import timezone

        now = timezone.now()

        queryset = cls.objects.filter(is_active=True)

        # Filter by placement
        if placement:
            queryset = queryset.filter(
                models.Q(placement=placement) | models.Q(placement="all")
            )

        # Filter by category
        if category:
            queryset = queryset.filter(
                models.Q(category=category) | models.Q(category__isnull=True)
            )

        # Filter by date range
        queryset = queryset.filter(
            models.Q(start_date__isnull=True) | models.Q(start_date__lte=now)
        ).filter(models.Q(end_date__isnull=True) | models.Q(end_date__gte=now))

        return queryset.order_by("display_order", "-created_at")

    def increment_view_count(self):
        """Increment the view count for this ad."""
        self.view_count = models.F("view_count") + 1
        self.save(update_fields=["view_count"])

    def increment_click_count(self):
        """Increment the click count for this ad."""
        self.click_count = models.F("click_count") + 1
        self.save(update_fields=["click_count"])


class Message(models.Model):
    """Model for messages between users related to an order."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shop_sent_messages",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shop_received_messages",
    )
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message from {self.sender} to {self.recipient} on order {self.order.order_number}"


class Notification(models.Model):
    """Model for user notifications."""

    NOTIFICATION_TYPE_CHOICES = [
        ("new_order", _("New Order")),
        ("new_review", _("New Review")),
        ("order_status_change", _("Order Status Change")),
        ("low_stock", _("Low Stock Warning")),
        ("general", _("General Announcement")),
    ]

    user = models.ForeignKey(
        MnoryUser, on_delete=models.CASCADE, related_name="shop_notifications"
    )
    notification_type = models.CharField(
        max_length=20, choices=NOTIFICATION_TYPE_CHOICES
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.URLField(
        max_length=500, blank=True, null=True, help_text=_("Link to the related object")
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")

    def __str__(self):
        return f"Notification for {self.user.email}: {self.title}"


class ChatbotQuestion(models.Model):
    user = models.ForeignKey(
        MnoryUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chatbot_questions",
    )
    question = models.TextField()
    answer = models.TextField()
    language_code = models.CharField(max_length=10, blank=True, null=True)
    source_path = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Chatbot question")
        verbose_name_plural = _("Chatbot questions")

    def __str__(self):
        return (self.question or "")[:100]


class Coupon(models.Model):
    """Model for discount coupons."""

    DISCOUNT_TYPE_CHOICES = [
        ("percentage", _("Percentage")),
        ("fixed", _("Fixed Amount")),
    ]

    code = models.CharField(
        max_length=50, unique=True, help_text=_("The code customers will enter.")
    )
    discount_type = models.CharField(
        max_length=10, choices=DISCOUNT_TYPE_CHOICES, default="percentage"
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_(
            "The discount value. If percentage, enter a number like 10 for 10%. If fixed, enter the amount."
        ),
    )
    min_purchase_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("The minimum cart total required to use this coupon."),
    )
    valid_from = models.DateTimeField(
        help_text=_("The date and time from which the coupon is valid.")
    )
    valid_to = models.DateTimeField(
        help_text=_("The date and time until which the coupon is valid.")
    )
    is_active = models.BooleanField(
        default=True, help_text=_("Whether the coupon is currently active.")
    )
    max_uses = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_("Maximum number of times this coupon can be used in total."),
    )
    max_uses_per_user = models.PositiveIntegerField(
        default=1,
        help_text=_("Maximum number of times a single user can use this coupon."),
    )
    times_used = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        verbose_name = _("Coupon")
        verbose_name_plural = _("Coupons")
        ordering = ["-valid_from"]

    def __str__(self):
        return self.code

    def is_valid(self):
        """Check if the coupon is currently valid."""
        now = timezone.now()
        return self.is_active and self.valid_from <= now and self.valid_to >= now
