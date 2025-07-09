from django.contrib import admin

from django.contrib import admin
from shop.models import (
    Category, SubCategory, FitType, Brand, Color, Size, 
    Product, ProductImage, ProductColor, ProductSize, ProductVariant , MnoryUser , VendorProfile
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'slug', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(FitType)
class FitTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ['name', 'hex_code', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'hex_code']

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ['name', 'size_type', 'order', 'is_active']
    list_filter = ['size_type', 'is_active']
    search_fields = ['name']
    ordering = ['size_type', 'order']

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
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'subcategory', 'brand', 'price', 
        'is_best_seller', 'is_new_arrival', 'is_on_sale', 'vendor',
        'is_active', 'created_at'
    ]
    list_filter = [
        'category', 'subcategory', 'brand', 'fit_type',
        'is_best_seller', 'is_new_arrival', 'is_on_sale', 'vendor',
        'is_featured', 'is_active', 'created_at'
    ]
    search_fields = ['name', 'description', 'brand__name']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ProductImageInline, ProductColorInline, ProductSizeInline, ProductVariantInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'short_description')
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
        ('Vendor', {
            'fields': ('vendor',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'alt_text', 'is_main', 'order', 'color', 'created_at']
    list_filter = ['is_main', 'color', 'created_at']
    search_fields = ['product__name', 'alt_text']

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'color', 'size', 'sku', 'stock_quantity', 'is_available']
    list_filter = ['color', 'size', 'is_available']
    search_fields = ['product__name', 'sku']


@admin.register(MnoryUser)
class MnoryUserAdmin(admin.ModelAdmin):
    list_display = ("email", "is_customer", "is_vendor", "is_staff")
    search_fields = ("email",)


@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user_email',
        'store_name',
        'profile_type',
        'product_count',
        'wallet_balance',
        'is_approved',
        'is_premium',
    )
    list_filter = ('profile_type', 'is_approved', 'country_of_operation')
    search_fields = ('user__email', 'store_name', 'country_of_operation')
    readonly_fields = ('product_count', 'wallet_balance', 'logo_preview', 'is_premium')
    autocomplete_fields = ('user',)
    fieldsets = (
        (None, {
            'fields': ('user', 'store_name', 'store_description', 'profile_type', 'is_approved')
        }),
        ('Media', {
            'fields': ('logo', 'logo_preview')
        }),
        ('Financials', {
            'fields': ('wallet_balance',)
        }),
        ('Other Info', {
            'fields': ('country_of_operation', 'website', 'product_count', 'is_premium')
        }),
    )

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "User Email"
    user_email.admin_order_field = "user__email"

    def logo_preview(self, obj):
        if obj.logo:
            return f'<img src="{obj.logo.url}" style="max-height: 100px;">'
        return "-"
    logo_preview.short_description = "Logo Preview"
    logo_preview.allow_tags = True
    logo_preview.allow_tags = True
    logo_preview.admin_order_field = "logo"
    logo_preview.allow_tags = True
    logo_preview.allow_tags = True
    logo_preview.allow_tags = True
    logo_preview.allow_tags = True
    logo_preview.allow_tags = True
    logo_preview.allow_tags = True
    logo_preview.allow_tags = True
    logo_preview.allow_tags = True
    logo_preview.allow_tags = True
    logo_preview.allow_tags = True

    class Media:
        css = {
            "all": ("admin/css/custom.css",)  # Optional: custom styling
        }

