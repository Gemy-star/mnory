# shop/models.py

from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from django.conf import settings # Import settings to get AUTH_USER_MODEL
from django.contrib.auth.models import AbstractUser
from shop.managers import MnoryUserManager
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from django.utils.translation import gettext_lazy as _

class MnoryUser(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_customer = models.BooleanField(default=True)
    is_vendor = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = MnoryUserManager()

    def __str__(self):
        return self.email

class VendorProfile(models.Model):
    """Vendor (Merchant) profile linked to User."""
    PROFILE_TYPE_CHOICES = [
        ('free', 'Free'),
        ('premium', 'Premium'),
    ]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vendorprofile")
    store_name = models.CharField(max_length=255, verbose_name="Store Name")
    store_description = models.TextField(null=True, blank=True, verbose_name="Store Description")
    logo = models.ImageField(upload_to="vendor_logos/", null=True, blank=True, verbose_name="Store Logo")
    website = models.URLField(null=True, blank=True, verbose_name="Store Website URL")
    product_count = models.PositiveIntegerField(default=0, verbose_name="Number of Products")
    country_of_operation = models.CharField(max_length=200, null=True, blank=True, verbose_name="Country of Operation")
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Wallet Balance")
    profile_type = models.CharField(max_length=10, choices=PROFILE_TYPE_CHOICES, default='free', verbose_name="Profile Type")
    is_approved = models.BooleanField(default=False)
    logo_resized = ImageSpecField(
        source='logo',
        processors=[ResizeToFill(1920, 600)],
        format='JPEG',
        options={'quality': 85}
    )
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    def __str__(self):
        return f"Vendor Profile for {self.user.email}"

    @property
    def is_premium(self) -> bool:
        return self.profile_type == 'premium'

    def update_product_count(self):
        """Update the count of products in the vendor's store."""
        self.product_count = self.user.products.count()  # Assuming related_name='products' on Product model
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
        if self.profile_type == 'premium':
            return True  # Already premium
        if self.wallet_balance >= settings.PREMIUM_UPGRADE_FEE:
            self.wallet_balance -= settings.PREMIUM_UPGRADE_FEE
            self.profile_type = 'premium'
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
        return reverse('shop:vendor_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.store_name

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('shop:category_detail', kwargs={'slug': self.slug})

class SubCategory(models.Model):
    category = models.ForeignKey(Category, related_name='subcategories', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='subcategories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Sub Categories"
        unique_together = ['category', 'slug']
        ordering = ['name']

    def __str__(self):
        return f"{self.category.name} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('shop:subcategory_detail', kwargs={'category_slug': self.category.slug, 'slug': self.slug})

class FitType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Color(models.Model):
    name = models.CharField(max_length=50, unique=True)
    hex_code = models.CharField(max_length=7, help_text="Color hex code (e.g., #FF0000)")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Size(models.Model):
    SIZE_TYPES = [
        ('clothing', 'Clothing'),
        ('shoes', 'Shoes'),
        ('accessories', 'Accessories'),
    ]
    
    name = models.CharField(max_length=20)
    size_type = models.CharField(max_length=20, choices=SIZE_TYPES, default='clothing')
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['size_type', 'order', 'name']
        unique_together = ['name', 'size_type']

    def __str__(self):
        return f"{self.name} ({self.get_size_type_display()})" # type: ignore
class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True)

    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    subcategory = models.ForeignKey(SubCategory, related_name='products', on_delete=models.CASCADE)
    fit_type = models.ForeignKey(FitType, related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
    brand = models.ForeignKey(Brand, related_name='products', on_delete=models.SET_NULL, null=True, blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal('0.01'))])

    # Flags
    is_best_seller = models.BooleanField(default=False)
    is_new_arrival = models.BooleanField(default=False)
    is_on_sale = models.BooleanField(default=False)  # Will be auto-set in save()
    is_featured = models.BooleanField(default=False)

    # Stock status
    stock_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)

    # SEO fields
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Many-to-many
    colors = models.ManyToManyField(Color, through='ProductColor', blank=True)
    sizes = models.ManyToManyField(Size, through='ProductSize', blank=True)

    #vendor
    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='products',
        on_delete=models.CASCADE,
        limit_choices_to={'is_vendor': True},
        null=True,
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['category', 'subcategory']),
            models.Index(fields=['is_active', 'is_available']),
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
        return reverse('shop:product_detail', kwargs={'slug': self.slug})

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
        """Return if total stock is above 0"""
        return self.stock_quantity > 0 or self.variants.filter(stock_quantity__gt=0, is_available=True).exists()

    def get_main_image(self):
        """Return the main image or fallback to first image"""
        main_image = self.images.filter(is_main=True).first()
        return main_image or self.images.first()

    def get_available_colors(self):
        """Return distinct active colors from variants"""
        return self.colors.filter(is_active=True, product_images__product=self).distinct()

    def get_available_sizes(self):
        """Return distinct active sizes from variants"""
        return self.sizes.filter(is_active=True, product=self).distinct()

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_main = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    color = models.ForeignKey(Color, related_name='product_images', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.product.name} - Image {self.order}"

    def save(self, *args, **kwargs):
        if self.is_main:
            # Ensure only one main image per product
            ProductImage.objects.filter(product=self.product, is_main=True).update(is_main=False)
        super().save(*args, **kwargs)

class ProductColor(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    color = models.ForeignKey(Color, on_delete=models.CASCADE)
    stock_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['product', 'color']

    def __str__(self):
        return f"{self.product.name} - {self.color.name}"

class ProductSize(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    stock_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['product', 'size']

    def __str__(self):
        return f"{self.product.name} - {self.size.name}"

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    color = models.ForeignKey(Color, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    sku = models.CharField(max_length=100, unique=True, blank=True)
    stock_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    price_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['product', 'color', 'size']

    def __str__(self):
        return f"{self.product.name} - {self.color.name} - {self.size.name}"

    @property
    def get_price(self):
        """Get the price for this variant"""
        base_price = self.product.get_price
        return base_price + self.price_adjustment

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = f"{self.product.slug}-{self.color.name.lower()}-{self.size.name.lower()}".replace(' ', '-')
        super().save(*args, **kwargs)

# --- Cart Models ---
class Cart(models.Model):
    session_key = models.CharField(max_length=40, null=True, blank=True, unique=True) # For anonymous users
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.OneToOneField(
        MnoryUser, 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cart'
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
        return self.items.aggregate(total_quantity=models.Sum('quantity'))['total_quantity'] or 0

    @property
    def total_price(self):
        return sum(item.get_total_price() for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product_variant') # A variant can only be in a cart once
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"

    def __str__(self):
        return f"{self.quantity} x {self.product_variant.product.name} ({self.product_variant.color.name}, {self.product_variant.size.name})"

    def get_total_price(self):
        return self.quantity * self.product_variant.get_price

# --- Wishlist Models ---
class Wishlist(models.Model):
    user = models.OneToOneField(MnoryUser, on_delete=models.CASCADE, related_name='wishlist')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Wishlist"
        verbose_name_plural = "Wishlists"

    def __str__(self):
        return f"Wishlist of {self.user.username}"

class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE) # Wishlist can be for a product, not necessarily a variant
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('wishlist', 'product') # A product can only be in a wishlist once
        verbose_name = "Wishlist Item"
        verbose_name_plural = "Wishlist Items"

    def __str__(self):
        return f"{self.product.name} in {self.wishlist.user.username}'s Wishlist"





class HomeSlider(models.Model):
    image = models.ImageField(upload_to='slider/', verbose_name=_("Slider Image"))
    # Processed image (1920x600)
    image_resized = ImageSpecField(
        source='image',
        processors=[ResizeToFill(1400, 650)],
        format='JPEG',
        options={'quality': 85}
    )

    alt_text = models.CharField(max_length=255, verbose_name=_("Alt Text"))
    heading = models.CharField(max_length=255, verbose_name=_("Heading"))
    subheading = models.TextField(verbose_name=_("Subheading"))
    button_text = models.CharField(max_length=100, verbose_name=_("Button Text"))
    button_url_name = models.URLField(
        max_length=100,
        verbose_name=_("URL Address"),
        help_text=_("Enter the URL Address")
    )
    order = models.PositiveIntegerField(default=0, verbose_name=_("Display Order"))
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))

    class Meta:
        ordering = ['order']
        verbose_name = _("Home Slider")
        verbose_name_plural = _("Home Sliders")

    def __str__(self):
        return self.heading
