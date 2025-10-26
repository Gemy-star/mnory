from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.db.models import Q, Min, Max, Sum, Count, F
from django.db.models.functions import TruncDay  # noqa
from django.views.decorators.http import (
    require_http_methods,
    require_POST,
    require_GET,
)  # noqa
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db import transaction, models, connection
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger  # noqa
import json
from .forms import (
    RegisterForm,
    LoginForm,
    ShippingAddressForm,
    PaymentForm,
    ReviewForm,
    CouponApplyForm,
    MessageForm,
    VendorShippingForm,
    PayoutRequestForm,
    ProductBulkEditForm,
)
from .models import (  # noqa
    Category,
    SubCategory,
    FitType,
    Brand,
    Color,
    Size,
    Product,
    ProductVariant,
    Cart,
    CartItem,
    Wishlist,
    WishlistItem,
    HomeSlider,
    Order,
    OrderItem,
    ShippingAddress,
    Payment,
    MnoryUser,
    VendorProfile,
    Advertisement,
    Coupon,
    Message,
    VendorShipping,
    VendorOrder,
)
from decimal import Decimal
import csv
from django.http import HttpResponse
from datetime import timedelta
import uuid
import logging
from django.utils.translation import gettext as _
from constance import config
from django.utils import timezone
from shop.models import Review

# Set up logger
logger = logging.getLogger(__name__)


# --- Helper Functions for Filtering/Sorting ---
def _filter_and_sort_products(products_queryset, request_get_params):
    """
    Applies common filtering and sorting logic to a product queryset.
    """
    subcategory_filter = request_get_params.get("subcategory")
    fit_type_filter = request_get_params.get("fit_type")
    brand_filter = request_get_params.get("brand")
    color_filter = request_get_params.get("color")
    size_filter = request_get_params.get("size")
    min_price_str = request_get_params.get("min_price")
    max_price_str = request_get_params.get("max_price")
    sort_by = request_get_params.get("sort", "name")

    if subcategory_filter:
        products_queryset = products_queryset.filter(
            subcategory__slug=subcategory_filter
        )

    if fit_type_filter:
        products_queryset = products_queryset.filter(fit_type__slug=fit_type_filter)

    if brand_filter:
        products_queryset = products_queryset.filter(brand__slug=brand_filter)

    if color_filter:
        # Filter products by color of their available variants
        products_queryset = products_queryset.filter(
            productvariant__color__slug=color_filter
        ).distinct()

    if size_filter:
        # Filter products by size of their available variants
        products_queryset = products_queryset.filter(
            productvariant__size__name__iexact=size_filter
        ).distinct()

    # Price filtering
    if min_price_str:
        try:
            min_price = Decimal(min_price_str)
            products_queryset = products_queryset.filter(price__gte=min_price)
        except (ValueError, TypeError):
            pass

    if max_price_str:
        try:
            max_price = Decimal(max_price_str)
            products_queryset = products_queryset.filter(price__lte=max_price)
        except (ValueError, TypeError):
            pass

    # Sorting
    if sort_by == "price_low":
        products_queryset = products_queryset.order_by("price")
    elif sort_by == "price_high":
        products_queryset = products_queryset.order_by("-price")
    elif sort_by == "newest":
        products_queryset = products_queryset.order_by("-created_at")
    elif sort_by == "popular":
        # Consider adding a sales count or view count to Product model for true popularity
        products_queryset = products_queryset.order_by("-is_best_seller", "-created_at")
    else:  # Default or invalid sort
        products_queryset = products_queryset.order_by("name")

    return (
        products_queryset.distinct()
    )  # Use distinct to avoid duplicates from many-to-many filters


def _serialize_products(products_queryset, request):
    """
    Helper function to serialize a queryset of products into a list of dictionaries.
    Handles prices, images, wishlist status, and other common fields.
    """
    products_data = []
    currency = request.session.get("currency", "USD")

    # Get user's wishlist items if authenticated
    products_in_wishlist_ids = set()
    if request.user.is_authenticated:
        try:
            wishlist = Wishlist.objects.only("id").get(user=request.user)
            products_in_wishlist_ids = set(
                wishlist.items.values_list("product_id", flat=True)
            )
        except Wishlist.DoesNotExist:
            pass

    for product in products_queryset:
        try:
            primary_image = product.get_main_image()
            hover_image = product.get_hover_image()

            image_url = (
                primary_image.image.url
                if primary_image
                else "/static/img/placeholder.jpg"
            )
            hover_image_url = (
                hover_image.image.url
                if hover_image and hover_image != primary_image
                else image_url
            )

            # Calculate price based on currency and sale status
            if currency == "EGP":
                display_price = (
                    f"{product.price_egp} EGP"
                    if product.is_on_sale
                    else f"{product.price_egp_no_sale} EGP"
                )
                original_price = (
                    f"{product.price_egp_no_sale} EGP" if product.is_on_sale else None
                )
            else:  # Default to USD
                display_price = (
                    f"{product.price_usd} USD"
                    if product.is_on_sale
                    else f"{product.price_usd_no_sale} USD"
                )
                original_price = (
                    f"{product.price_usd_no_sale} USD" if product.is_on_sale else None
                )

            # Vendor information
            vendor_name = None
            vendor_slug = None
            if product.vendor and hasattr(product.vendor, "vendorprofile"):
                vendor_name = product.vendor.vendorprofile.store_name
                vendor_slug = product.vendor.vendorprofile.slug

            products_data.append(
                {
                    "id": product.pk,
                    "name": product.name,
                    "slug": product.slug,
                    "price": display_price,
                    "original_price": original_price,
                    "image": image_url,
                    "hover_image": hover_image_url,
                    "url": product.get_absolute_url(),
                    "is_on_sale": product.is_on_sale,
                    "is_featured": product.is_featured,
                    "is_new_arrival": product.is_new_arrival,
                    "is_best_seller": getattr(product, "is_best_seller", False),
                    "is_in_stock": product.is_in_stock,
                    "discount_percentage": product.get_discount_percentage(),
                    "in_wishlist": product.pk in products_in_wishlist_ids,
                    "vendor_name": vendor_name,
                    "vendor_slug": vendor_slug,
                    "brand": product.brand.name if product.brand else None,
                    "category": product.category.name if product.category else None,
                }
            )
        except Exception as e:
            logger.warning(
                f"Could not serialize product {product.id} ('{product.name}'): {e}"
            )
            continue

    return products_data


# --- Core Product & Category Views ---
def home(request):
    """Homepage view"""
    # Optimized initial product queries to reduce database hits - excluding obvious dummy/test products
    # Use prefetch_related for images and select_related for foreign keys
    base_products = (
        Product.objects.filter(is_active=True, is_available=True)
        .exclude(name__icontains="test product")
        .exclude(name__icontains="dummy product")
        .exclude(name__icontains="sample product")
        .exclude(name__startswith="Test")
        .exclude(name__startswith="Dummy")
        .exclude(description__icontains="this is a test")
        .exclude(description__icontains="dummy description")
        .exclude(description__icontains="sample description")
        .prefetch_related("images")
        .select_related("category", "subcategory", "brand")
        .distinct()
    )
    featured_products = base_products.filter(is_featured=True).distinct()[:8]
    new_arrivals = base_products.filter(is_new_arrival=True).distinct()[:8]
    best_sellers = base_products.filter(is_best_seller=True).distinct()[:8]
    all_products_recent = base_products.order_by("-created_at").distinct()[
        :12
    ]  # Get 12 for category tabs
    sale_products = base_products.filter(is_on_sale=True).distinct()[:8]

    categories = Category.objects.filter(is_active=True).order_by("name")
    sliders = HomeSlider.objects.filter(is_active=True).order_by("order")

    # Get active advertisements for home page
    home_ads = Advertisement.get_active_ads(placement="home")

    # Use the new serializer helper for the JSON data for category tabs
    initial_category_products_json = json.dumps(
        _serialize_products(all_products_recent, request)
    )

    context = {
        "featured_products": featured_products,
        "new_arrivals": new_arrivals,
        "best_sellers": best_sellers,
        "sale_products": sale_products,
        "categories": categories,
        "sliders": sliders,
        "home_ads": home_ads,  # Add advertisements to context
        "all_products": all_products_recent,  # Pass raw queryset for template rendering
        "initial_category_products": all_products_recent,  # For category tabs section
        "initial_category_products_json": initial_category_products_json,
        "currency": request.session.get("currency", "USD"),  # Add currency for template
    }

    return render(request, "shop/home.html", context)


@require_GET
def get_category_products_api(request):
    """API endpoint to get products by category for AJAX filtering"""
    try:
        category_slug = request.GET.get("category", "all")

        # Base query for active products - excluding obvious dummy/test products
        base_products = (
            Product.objects.filter(is_active=True, is_available=True)
            .exclude(name__icontains="test product")
            .exclude(name__icontains="dummy product")
            .exclude(name__icontains="sample product")
            .exclude(name__startswith="Test")
            .exclude(name__startswith="Dummy")
            .exclude(description__icontains="this is a test")
            .exclude(description__icontains="dummy description")
            .exclude(description__icontains="sample description")
            .prefetch_related("images")
            .select_related("category", "subcategory", "brand", "vendor")
            .distinct()
        )

        # Filter by category if not 'all'
        if category_slug and category_slug != "all":
            try:
                category = Category.objects.get(slug=category_slug, is_active=True)
                products = base_products.filter(category=category)[
                    :12
                ]  # Limit to 12 products
            except Category.DoesNotExist:
                return JsonResponse({"error": "Category not found"}, status=404)
        else:
            products = base_products.order_by("-created_at")[
                :12
            ]  # Show recent products

        # Use the refactored serializer
        products_data = _serialize_products(products, request)

        return JsonResponse({"success": True, "products": products_data})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e), "products": []})


def category_detail(request, slug):
    """Category detail view - supports 'all' to show all products"""
    category = None
    subcategories = []
    # Start with active and available products
    products_queryset = (
        Product.objects.filter(is_active=True, is_available=True)
        .prefetch_related("images")
        .select_related("category", "subcategory", "brand")
    )

    if slug and slug != "all":
        category = get_object_or_404(Category, slug=slug, is_active=True)
        subcategories = category.subcategories.filter(is_active=True).order_by("name")
        products_queryset = products_queryset.filter(category=category)
    elif not slug or slug == "all":
        # If slug is 'all', products_queryset remains unfiltered by category
        pass
    else:
        messages.error(request, _("Invalid category selected."))
        return redirect("shop:home")  # Redirect to home or all products view

    # Get active advertisements for this category
    from .models import Advertisement

    category_ads = (
        Advertisement.get_active_ads(placement="category", category=category)
        if category
        else []
    )

    # Apply filters and sorting using helper. Pass request object to helper for messages
    products_queryset = _filter_and_sort_products(products_queryset, request.GET)

    # Price range calculation for the *entire* filtered set, before pagination
    price_range = products_queryset.aggregate(Min("price"), Max("price"))

    # Pagination
    per_page = request.GET.get("per_page")
    try:
        per_page = int(per_page)
        if per_page not in [12, 24, 48]:
            per_page = 12
    except (TypeError, ValueError):
        per_page = 12
    paginator = Paginator(products_queryset, per_page)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # --- Performance Optimization for Filter Options ---
    # Instead of filtering on the entire queryset, we get the IDs first.
    # This is much faster than passing a large subquery in the `__in` clause.
    product_ids = products_queryset.values_list("id", flat=True)

    # Get FitType options
    fit_type_ids = (
        products_queryset.exclude(fit_type__isnull=True)
        .values_list("fit_type_id", flat=True)
        .distinct()
    )
    fit_types = FitType.objects.filter(is_active=True, id__in=fit_type_ids).order_by(
        "name"
    )

    # Get Brand options
    brand_ids = (
        products_queryset.exclude(brand__isnull=True)
        .values_list("brand_id", flat=True)
        .distinct()
    )
    brands = Brand.objects.filter(is_active=True, id__in=brand_ids).order_by("name")

    # Get Color and Size options from available variants of the filtered products
    variants_of_products = ProductVariant.objects.filter(
        product_id__in=product_ids, is_available=True, stock_quantity__gt=0
    )
    color_ids = variants_of_products.values_list("color_id", flat=True).distinct()
    colors = Color.objects.filter(is_active=True, id__in=color_ids).order_by("name")

    size_ids = variants_of_products.values_list("size_id", flat=True).distinct()
    sizes = Size.objects.filter(is_active=True, id__in=size_ids).order_by("name")

    all_categories = Category.objects.filter(is_active=True).order_by(
        "name"
    )  # For navbar/sidebar
    products_in_wishlist_ids = []
    if request.user.is_authenticated:
        try:
            wishlist = Wishlist.objects.only("id").get(user=request.user)
            products_in_wishlist_ids = list(
                wishlist.items.values_list("product_id", flat=True)
            )
        except Wishlist.DoesNotExist:
            pass

    context = {
        "category": category,
        "subcategories": subcategories,
        "products": page_obj,  # This is the paginated queryset
        "fit_types": fit_types,
        "brands": brands,
        "colors": colors,
        "sizes": sizes,
        "price_range": price_range,
        "categories": all_categories,
        "category_ads": category_ads,  # Add advertisements for category
        "products_in_wishlist_ids": products_in_wishlist_ids,
        "current_filters": {
            "subcategory": request.GET.get("subcategory"),
            "fit_type": request.GET.get("fit_type"),
            "brand": request.GET.get("brand"),
            "color": request.GET.get("color"),
            "size": request.GET.get("size"),
            "min_price": request.GET.get("min_price"),
            "max_price": request.GET.get("max_price"),
            "sort": request.GET.get("sort", "name"),
        },
    }

    return render(request, "shop/category_detail.html", context)


def subcategory_detail(request, category_slug, slug):
    """Subcategory detail view"""
    category = get_object_or_404(Category, slug=category_slug, is_active=True)
    subcategory = get_object_or_404(
        SubCategory, slug=slug, category=category, is_active=True
    )

    products_queryset = (
        Product.objects.filter(
            subcategory=subcategory, is_active=True, is_available=True
        )
        .prefetch_related("images")
        .select_related("category", "subcategory", "brand")
    )

    # Apply filters and sorting using helper
    products_queryset = _filter_and_sort_products(products_queryset, request.GET)

    # Price range calculation for current filtered set
    price_range = products_queryset.aggregate(Min("price"), Max("price"))

    # Pagination
    per_page = request.GET.get("per_page")
    try:
        per_page = int(per_page)
        if per_page not in [12, 24, 48]:
            per_page = 12
    except (TypeError, ValueError):
        per_page = 12
    paginator = Paginator(products_queryset, per_page)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Get filter options relevant to this subcategory's products
    fit_types = (
        FitType.objects.filter(is_active=True, products__in=products_queryset)
        .distinct()
        .order_by("name")
    )
    brands = (
        Brand.objects.filter(is_active=True, products__in=products_queryset)
        .distinct()
        .order_by("name")
    )
    colors = (
        Color.objects.filter(
            is_active=True, productvariant__product__in=products_queryset
        )
        .distinct()
        .order_by("name")
    )
    sizes = (
        Size.objects.filter(
            is_active=True, productvariant__product__in=products_queryset
        )
        .distinct()
        .order_by("name")
    )

    all_categories = Category.objects.filter(is_active=True).order_by(
        "name"
    )  # For sidebar navigation

    products_in_wishlist_ids = []
    if request.user.is_authenticated:
        try:
            wishlist = Wishlist.objects.only("id").get(user=request.user)
            products_in_wishlist_ids = list(
                wishlist.items.values_list("product_id", flat=True)
            )
        except Wishlist.DoesNotExist:
            pass

    context = {
        "category": category,
        "subcategory": subcategory,
        "products": page_obj,
        "fit_types": fit_types,
        "brands": brands,
        "colors": colors,
        "sizes": sizes,
        "price_range": price_range,
        "categories": all_categories,
        "subcategories": category.subcategories.filter(is_active=True).order_by("name"),
        "products_in_wishlist_ids": products_in_wishlist_ids,
        "current_filters": {
            "subcategory": request.GET.get(
                "subcategory"
            ),  # This will be the current subcategory
            "fit_type": request.GET.get("fit_type"),
            "brand": request.GET.get("brand"),
            "color": request.GET.get("color"),
            "size": request.GET.get("size"),
            "min_price": request.GET.get("min_price"),
            "max_price": request.GET.get("max_price"),
            "sort": request.GET.get("sort", "name"),
        },
    }

    return render(request, "shop/subcategory_detail.html", context)


def product_detail(request, slug):
    """Product detail view"""
    product = get_object_or_404(
        Product.objects.select_related(
            "category", "subcategory", "brand", "fit_type"
        ).prefetch_related("images", "variants__color", "variants__size"),
        slug=slug,
        is_active=True,
        is_available=True,
    )

    related_products = (
        Product.objects.filter(
            Q(category=product.category) | Q(subcategory=product.subcategory),
            is_active=True,
            is_available=True,
        )
        .exclude(id=product.id)
        .distinct()
        .prefetch_related("images", "variants__color", "variants__size")
        .select_related("category", "subcategory", "brand")[:8]
    )

    variants = product.variants.filter(is_available=True, stock_quantity__gt=0)

    available_colors = product.get_available_colors()
    available_sizes = product.get_available_sizes()

    product_images = product.images.all().order_by("order")

    categories = Category.objects.filter(is_active=True).order_by("name")

    is_in_wishlist = False
    if request.user.is_authenticated:
        is_in_wishlist = WishlistItem.objects.filter(
            wishlist__user=request.user, product=product
        ).exists()

    reviews = (
        product.reviews.filter(is_public=True)
        .select_related("user")
        .order_by("-created_at")
    )
    review_form = ReviewForm()
    user_can_review = False
    if request.user.is_authenticated:
        user_can_review = (
            OrderItem.objects.filter(
                order__user=request.user,
                product_variant__product=product,
                order__status="delivered",
            ).exists()
            and not reviews.filter(user=request.user).exists()
        )

    context = {
        "product": product,
        "related_products": related_products,
        "variants": variants,
        "available_colors": available_colors,
        "available_sizes": available_sizes,  # This will now be ordered by size_type, then 'order', then 'name'
        "product_images": product_images,
        "categories": categories,
        "is_in_wishlist": is_in_wishlist,
        "reviews": reviews,
        "review_form": review_form,
        "user_can_review": user_can_review,
    }

    return render(request, "shop/product_detail.html", context)


@login_required
@require_POST
def submit_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    form = ReviewForm(request.POST)

    if form.is_valid():
        # Check if user has purchased this product
        can_review = OrderItem.objects.filter(
            order__user=request.user,
            product_variant__product=product,
            order__status="delivered",
        ).exists()
        if not can_review:
            messages.error(
                request,
                _("You can only review products you have purchased and received."),
            )
            return redirect(product.get_absolute_url())

        review = form.save(commit=False)
        review.product = product
        review.user = request.user
        review.save()
        messages.success(request, _("Thank you for your review!"))
    else:
        messages.error(
            request,
            _("There was an error with your submission. Please check the form."),
        )

    return redirect(product.get_absolute_url())


# --- Search & API Endpoints ---
@require_http_methods(["GET"])
def product_search_view(request):
    """
    Display product search results on a dedicated page.
    """
    query = request.GET.get("q", "").strip()
    products_list = Product.objects.none()

    if query:
        products_list = (
            Product.objects.filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(brand__name__icontains=query)
                | Q(category__name__icontains=query),
                is_active=True,
                is_available=True,
            )
            .select_related("category", "brand")
            .prefetch_related("images")
            .distinct()
        )

    paginator = Paginator(products_list, 12)  # 12 products per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "query": query,
        "products": page_obj,
        "result_count": paginator.count,
    }
    return render(request, "shop/search_results.html", context)


@require_http_methods(["GET"])
def get_product_variants(request, product_id):
    """
    AJAX endpoint to get product variants based on color and size filters.
    Returns a list of matching variants with stock info.
    """
    try:
        product = get_object_or_404(Product, id=product_id)
    except ValueError:
        return JsonResponse(
            {"variants": [], "message": _("Invalid product ID.")}, status=400
        )

    color_id = request.GET.get("color")
    size_id = request.GET.get("size")

    variants_queryset = ProductVariant.objects.filter(
        product=product,
        is_available=True,
        stock_quantity__gt=0,  # Only show variants that are in stock
    ).select_related(
        "color", "size"
    )  # Efficiently fetch related color and size objects

    if color_id:
        try:
            variants_queryset = variants_queryset.filter(color__id=int(color_id))
        except (ValueError, TypeError):
            # If color_id is invalid, return empty results (or all if that's desired behavior)
            return JsonResponse(
                {"variants": [], "message": _("Invalid color ID.")}, status=400
            )

    if size_id:
        try:
            variants_queryset = variants_queryset.filter(size__id=int(size_id))
        except (ValueError, TypeError):
            # If size_id is invalid, return empty results
            return JsonResponse(
                {"variants": [], "message": _("Invalid size ID.")}, status=400
            )

    results = []
    for variant in variants_queryset:
        results.append(
            {
                "id": variant.id,
                "color_id": variant.color.id if variant.color else None,
                "color_name": variant.color.name if variant.color else _("N/A"),
                "size_id": variant.size.id if variant.size else None,
                "size_name": variant.size.name if variant.size else _("N/A"),
                "price": str(
                    variant.get_price()
                ),  # Ensure Decimal is serialized as string
                "stock": variant.stock_quantity,
                "sku": variant.sku,
            }
        )

    return JsonResponse({"variants": results})


@require_GET
def get_cart_and_wishlist_counts(request):
    """
    Returns JSON with counts of items in cart and wishlist.
    Supports logged-in users and anonymous users (session).
    """
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        cart_count = cart.total_items if cart else 0
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.save()
            session_key = request.session.session_key
        cart = Cart.objects.filter(session_key=session_key).first()
        cart_count = cart.total_items if cart else 0

    if request.user.is_authenticated:
        wishlist = Wishlist.objects.filter(user=request.user).first()
        wishlist_count = wishlist.items.count() if wishlist else 0
    else:
        wishlist_session = request.session.get("wishlist", [])
        wishlist_count = len(wishlist_session)

    return JsonResponse(
        {
            "success": True,
            "cart_count": cart_count,
            "wishlist_count": wishlist_count,
        }
    )


def get_shipping_cost(request):
    """
    AJAX endpoint. Returns total shipping cost based on the selected city and items in the cart.
    """
    city = request.GET.get("city", "")
    cart = get_cart_for_request(request)
    total_shipping_cost = Decimal("0.00")

    if cart:
        # Group cart items by vendor
        vendor_items = {}
        for item in cart.items.all():
            vendor_id = item.product_variant.product.vendor_id
            if vendor_id not in vendor_items:
                vendor_items[vendor_id] = []
            vendor_items[vendor_id].append(item)

        # Calculate shipping for each vendor's sub-order
        for vendor_id, items in vendor_items.items():
            vendor_shipping = VendorShipping.objects.filter(vendor_id=vendor_id).first()
            if vendor_shipping:
                subtotal = sum(item.get_total_price() for item in items)
                if not (
                    vendor_shipping.free_shipping_threshold
                    and subtotal >= vendor_shipping.free_shipping_threshold
                ):
                    if city == "OUTSIDE_CAIRO":
                        total_shipping_cost += (
                            vendor_shipping.shipping_rate_outside_cairo
                        )
                    else:  # Default to inside Cairo
                        total_shipping_cost += vendor_shipping.shipping_rate_cairo

    return JsonResponse({"success": True, "shipping_cost": float(total_shipping_cost)})


# --- Wishlist Views ---
def wishlist_view(request):
    """Displays the user's wishlist with pagination."""
    products_qs = Product.objects.none()
    products_in_wishlist_ids = set()
    if request.user.is_authenticated:
        try:
            wishlist = request.user.wishlist
            products_qs = (
                Product.objects.filter(wishlistitem__wishlist=wishlist)
                .select_related("category", "subcategory", "brand")
                .prefetch_related("images", "variants__color", "variants__size")
                .order_by("name")
            )
            products_in_wishlist_ids = set(
                wishlist.items.values_list("product_id", flat=True)
            )
        except Wishlist.DoesNotExist:
            products_qs = Product.objects.none()
            products_in_wishlist_ids = set()
    else:
        wishlist_session = request.session.get("wishlist", [])
        if wishlist_session:
            products_qs = (
                Product.objects.filter(id__in=wishlist_session)
                .select_related("category", "subcategory", "brand")
                .prefetch_related("images")
                .order_by("name")
            )
            products_in_wishlist_ids = set(wishlist_session)
        else:
            products_qs = Product.objects.none()
            products_in_wishlist_ids = set()

    # Pagination: 8 products per page
    paginator = Paginator(products_qs, 8)
    page = request.GET.get("page", 1)
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    # Update wishlist count in session
    request.session["wishlist_count"] = products_qs.count()

    context = {
        "products": products,
        "products_in_wishlist_ids": products_in_wishlist_ids,
    }
    return render(request, "shop/wishlist_view.html", context)


@require_POST
def add_to_cart(request):
    # Determine current language
    lang = getattr(request, "LANGUAGE_CODE", "en")

    try:
        if request.content_type and request.content_type.startswith("application/json"):
            try:
                data = json.loads(request.body)
            except Exception:
                data = {}
        else:
            data = request.POST
        product_variant_id = data.get("product_variant_id")
        product_id = data.get("product_id")
        color_id = data.get("color_id")
        size_id = data.get("size_id")
        try:
            quantity = int(data.get("quantity", 1))
        except (ValueError, TypeError):
            quantity = 1
    except Exception:
        message = "Invalid data provided." if lang == "en" else "بيانات غير صالحة."
        return JsonResponse({"success": False, "message": message}, status=400)

    product_variant = None
    product = None

    # If color and size are provided, find the variant
    if color_id and size_id and product_id:
        try:
            product = Product.objects.get(
                id=product_id, is_active=True, is_available=True
            )
            product_variant = ProductVariant.objects.filter(
                product=product,
                color_id=color_id,
                size_id=size_id,
                is_available=True,
                stock_quantity__gt=0,
            ).first()

            if not product_variant:
                message = (
                    "This color and size combination is not available."
                    if lang == "en"
                    else "هذا المزيج من اللون والحجم غير متاح."
                )
                return JsonResponse({"success": False, "message": message}, status=400)
        except Product.DoesNotExist:
            message = (
                "Product not found or not available."
                if lang == "en"
                else "المنتج غير موجود أو غير متوفر."
            )
            return JsonResponse({"success": False, "message": message}, status=404)
    elif product_variant_id:
        try:
            product_variant = ProductVariant.objects.get(
                id=product_variant_id, is_available=True
            )
            product = product_variant.product
        except ProductVariant.DoesNotExist:
            message = (
                "Product variant not found or not available."
                if lang == "en"
                else "النسخة المحددة من المنتج غير موجودة أو غير متوفرة."
            )
            return JsonResponse({"success": False, "message": message}, status=404)
    elif product_id:
        try:
            product = Product.objects.get(
                id=product_id, is_active=True, is_available=True
            )
            product_variant = (
                ProductVariant.objects.filter(
                    product=product, is_available=True, stock_quantity__gt=0
                )
                .order_by("pk")
                .first()
            )
            if not product_variant:
                message = (
                    f"No available variants for {product.name} or out of stock."
                    if lang == "en"
                    else f"لا توجد نسخ متاحة لـ {product.name} أو نفدت الكمية."
                )
                return JsonResponse({"success": False, "message": message}, status=400)
        except Product.DoesNotExist:
            message = (
                "Product not found or not available."
                if lang == "en"
                else "المنتج غير موجود أو غير متوفر."
            )
            return JsonResponse({"success": False, "message": message}, status=404)
    else:
        message = (
            "Product or variant not provided."
            if lang == "en"
            else "لم يتم تقديم منتج أو نسخة."
        )
        return JsonResponse({"success": False, "message": message}, status=400)

    if quantity <= 0:
        message = (
            "Quantity must be at least 1."
            if lang == "en"
            else "يجب أن تكون الكمية على الأقل 1."
        )
        return JsonResponse({"success": False, "message": message}, status=400)

    if product_variant.stock_quantity < quantity:
        message = (
            (
                f'Not enough stock for {product.name} ({product_variant.color.name if product_variant.color else "N/A"}, '
                f'{product_variant.size.name if product_variant.size else "N/A"}). Available: {product_variant.stock_quantity}.'
            )
            if lang == "en"
            else (
                f'الكمية غير كافية للمنتج {product.name} ({product_variant.color.name if product_variant.color else "غير متوفر"}, '
                f'{product_variant.size.name if product_variant.size else "غير متوفر"}). المتوفر: {product_variant.stock_quantity}.'
            )
        )
        return JsonResponse({"success": False, "message": message}, status=400)

    with transaction.atomic():
        if request.user.is_authenticated:
            cart, created = Cart.objects.select_for_update().get_or_create(
                user=request.user
            )
        else:
            session_key = request.session.session_key
            if not session_key:
                request.session.save()
                session_key = request.session.session_key
            cart, created = Cart.objects.select_for_update().get_or_create(
                session_key=session_key
            )

        cart_item, created = CartItem.objects.select_for_update().get_or_create(
            cart=cart, product_variant=product_variant, defaults={"quantity": quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        request.session["cart_count"] = cart.total_items
        message = (
            "Item added to cart successfully!"
            if lang == "en"
            else "تمت إضافة العنصر إلى السلة بنجاح!"
        )
        return JsonResponse(
            {"success": True, "message": message, "cart_total_items": cart.total_items}
        )


@require_POST
def add_to_wishlist(request):
    lang = getattr(request, "LANGUAGE_CODE", "en")
    try:
        if request.content_type and request.content_type.startswith("application/json"):
            try:
                data = json.loads(request.body)
            except Exception:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Invalid JSON." if lang == "en" else "نص غير صالح.",
                    },
                    status=400,
                )
        else:
            data = request.POST
        product_id = data.get("product_id")
        if not product_id:
            return JsonResponse(
                {
                    "success": False,
                    "message": (
                        "Product ID not provided."
                        if lang == "en"
                        else "معرف المنتج غير موجود."
                    ),
                },
                status=400,
            )
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return JsonResponse(
                {
                    "success": False,
                    "message": (
                        "Product not found." if lang == "en" else "المنتج غير موجود."
                    ),
                },
                status=404,
            )

        if request.user.is_authenticated:
            with transaction.atomic():
                wishlist, created = Wishlist.objects.select_for_update().get_or_create(
                    user=request.user
                )
                wishlist_item, item_created = WishlistItem.objects.get_or_create(
                    wishlist=wishlist, product=product
                )
                if item_created:
                    message = (
                        "Item added to wishlist successfully!"
                        if lang == "en"
                        else "تمت إضافة العنصر إلى قائمة الرغبات بنجاح!"
                    )
                    status = "added"
                else:
                    message = (
                        "Item is already in your wishlist."
                        if lang == "en"
                        else "العنصر موجود بالفعل في قائمة رغباتك."
                    )
                    status = "exists"
                wishlist_count = wishlist.items.count()
        else:
            wishlist_session = request.session.get("wishlist", [])
            if str(product_id) in wishlist_session:
                message = (
                    "Item is already in your wishlist."
                    if lang == "en"
                    else "العنصر موجود بالفعل في قائمة رغباتك."
                )
                status = "exists"
            else:
                wishlist_session.append(str(product_id))
                request.session["wishlist"] = wishlist_session
                message = (
                    "Item added to wishlist successfully!"
                    if lang == "en"
                    else "تمت إضافة العنصر إلى قائمة الرغبات بنجاح!"
                )
                status = "added"
            wishlist_count = len(wishlist_session)

        request.session["wishlist_count"] = wishlist_count
        return JsonResponse(
            {
                "success": True,
                "message": message,
                "status": status,
                "wishlist_total_items": wishlist_count,
            }
        )
    except Exception:
        message = "An error occurred." if lang == "en" else "حدث خطأ."
        return JsonResponse({"success": False, "message": message}, status=500)


@require_POST
def remove_from_wishlist(request):
    lang = getattr(request, "LANGUAGE_CODE", "en")
    try:
        if request.content_type and request.content_type.startswith("application/json"):
            try:
                data = json.loads(request.body)
            except Exception:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Invalid JSON." if lang == "en" else "نص غير صالح.",
                    },
                    status=400,
                )
        else:
            data = request.POST
        product_id = data.get("product_id")
        if not product_id:
            return JsonResponse(
                {
                    "success": False,
                    "message": (
                        "Product ID not provided."
                        if lang == "en"
                        else "معرف المنتج غير موجود."
                    ),
                },
                status=400,
            )
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return JsonResponse(
                {
                    "success": False,
                    "message": (
                        "Product not found." if lang == "en" else "المنتج غير موجود."
                    ),
                },
                status=404,
            )

        if request.user.is_authenticated:
            try:
                wishlist = Wishlist.objects.get(user=request.user)
            except Wishlist.DoesNotExist:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Wishlist not found for user.",
                        "status": "wishlist_missing",
                    },
                    status=404,
                )
            with transaction.atomic():
                deleted_count, _ = WishlistItem.objects.filter(
                    wishlist=wishlist, product=product
                ).delete()
                if deleted_count > 0:
                    wishlist_count = wishlist.items.count()
                    request.session["wishlist_count"] = wishlist_count
                    message = (
                        "Item removed successfully!"
                        if lang == "en"
                        else "تمت إزالة العنصر بنجاح!"
                    )
                    return JsonResponse(
                        {
                            "success": True,
                            "message": message,
                            "wishlist_total_items": wishlist_count,
                            "status": "removed",
                        }
                    )
                else:
                    message = (
                        "Item not found in wishlist."
                        if lang == "en"
                        else "العنصر غير موجود في قائمة الرغبات."
                    )
                    return JsonResponse(
                        {"success": False, "message": message, "status": "not_found"},
                        status=404,
                    )
        else:
            wishlist_session = request.session.get("wishlist", [])
            if str(product_id) in wishlist_session:
                wishlist_session.remove(str(product_id))
                request.session["wishlist"] = wishlist_session
                wishlist_count = len(wishlist_session)
                request.session["wishlist_count"] = wishlist_count
                message = (
                    "Item removed successfully!"
                    if lang == "en"
                    else "تمت إزالة العنصر بنجاح!"
                )
                return JsonResponse(
                    {
                        "success": True,
                        "message": message,
                        "wishlist_total_items": wishlist_count,
                        "status": "removed",
                    }
                )
            else:
                message = (
                    "Item not found in wishlist."
                    if lang == "en"
                    else "العنصر غير موجود في قائمة الرغبات."
                )
                return JsonResponse(
                    {"success": False, "message": message, "status": "not_found"},
                    status=404,
                )
    except Exception:
        message = "An error occurred." if lang == "en" else "حدث خطأ."
        return JsonResponse({"success": False, "message": message}, status=500)


@require_POST
def remove_from_cart(request):
    lang = getattr(request, "LANGUAGE_CODE", "en")
    try:
        if request.content_type and request.content_type.startswith("application/json"):
            try:
                data = json.loads(request.body)
            except Exception:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Invalid JSON." if lang == "en" else "نص غير صالح.",
                    },
                    status=HttpResponseBadRequest.status_code,
                )
        else:
            data = request.POST
        cart_item_id = data.get("cart_item_id")
        if not cart_item_id:
            return JsonResponse(
                {
                    "success": False,
                    "message": (
                        "Cart item ID not provided."
                        if lang == "en"
                        else "معرف عنصر السلة غير موجود."
                    ),
                },
                status=HttpResponseBadRequest.status_code,
            )
        try:
            cart_item_id = int(cart_item_id)
        except ValueError:
            return JsonResponse(
                {
                    "success": False,
                    "message": (
                        "Invalid cart item ID format."
                        if lang == "en"
                        else "تنسيق معرف عنصر السلة غير صالح."
                    ),
                },
                status=HttpResponseBadRequest.status_code,
            )
        try:
            cart_item = get_object_or_404(
                CartItem.objects.select_related("cart"), id=cart_item_id
            )
            if request.user.is_authenticated:
                if cart_item.cart.user != request.user:
                    return JsonResponse(
                        {
                            "success": False,
                            "message": (
                                "Unauthorized action."
                                if lang == "en"
                                else "إجراء غير مصرح به."
                            ),
                        },
                        status=HttpResponseForbidden.status_code,
                    )
            else:
                if cart_item.cart.session_key != request.session.session_key:
                    return JsonResponse(
                        {
                            "success": False,
                            "message": (
                                "Unauthorized action."
                                if lang == "en"
                                else "إجراء غير مصرح به."
                            ),
                        },
                        status=HttpResponseForbidden.status_code,
                    )
            cart = cart_item.cart
            with transaction.atomic():
                cart_item.delete()
                request.session["cart_count"] = cart.total_items
                message = (
                    "Item removed from cart."
                    if lang == "en"
                    else "تمت إزالة العنصر من السلة."
                )
                return JsonResponse(
                    {
                        "success": True,
                        "message": message,
                        "cart_item_id": cart_item_id,
                        "cart_total_items": cart.total_items,
                        "cart_total_price": str(cart.total_price),
                    }
                )
        except CartItem.DoesNotExist:
            message = (
                "Cart item not found."
                if lang == "en"
                else "لم يتم العثور على عنصر في السلة."
            )
            return JsonResponse({"success": False, "message": message}, status=404)
        except Exception as e:
            return JsonResponse(
                {
                    "success": False,
                    "message": f"An unexpected error occurred: {str(e)}",
                },
                status=500,
            )
    except Exception:
        message = "An error occurred." if lang == "en" else "حدث خطأ."
        return JsonResponse({"success": False, "message": message}, status=500)


# --- Cart Views ---
def cart_view(request):
    cart_items_data = []
    total_cart_price = Decimal("0.00")
    shipping_fee = Decimal(config.SHIPPING_RATE_CAIRO)
    cart = None
    coupon_apply_form = CouponApplyForm()

    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            pass
    else:
        session_key = request.session.session_key
        if session_key:
            try:
                cart = Cart.objects.get(session_key=session_key)
            except Cart.DoesNotExist:
                pass

    if cart:
        cart_items = cart.items.select_related(
            "product_variant__product",
            "product_variant__color",
            "product_variant__size",
        ).order_by("pk")

        for item in cart_items:
            current_stock = (
                item.product_variant.stock_quantity if item.product_variant else 0
            )
            if item.quantity > current_stock:
                item.quantity = current_stock
                item.save()

            if current_stock == 0:
                item.delete()
                continue

            item_total = item.get_total_price()
            total_cart_price += item_total
            cart_items_data.append(
                {
                    "id": item.id,
                    "variant": item.product_variant,
                    "quantity": item.quantity,
                    "total": item_total,
                    "stock_available": current_stock,
                }
            )

        cart.update_totals()
        total_cart_price = cart.total_price_field
        request.session["cart_count"] = cart.total_items_field
    else:
        request.session["cart_count"] = 0

    # --- Coupon Logic ---
    coupon_id = request.session.get("coupon_id")
    discount_amount = Decimal("0.00")
    coupon = None
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            if coupon.is_valid():
                if (
                    coupon.min_purchase_amount
                    and total_cart_price < coupon.min_purchase_amount
                ):
                    messages.warning(
                        request,
                        _(
                            f"Cart total must be at least {coupon.min_purchase_amount} to use this coupon."
                        ),
                    )
                    # Remove invalid coupon
                    del request.session["coupon_id"]
                else:
                    if coupon.discount_type == "percentage":
                        discount_amount = (
                            total_cart_price * coupon.discount_value
                        ) / 100
                    else:  # Fixed amount
                        discount_amount = coupon.discount_value
            else:
                del request.session["coupon_id"]  # Coupon is no longer valid
        except Coupon.DoesNotExist:
            del request.session["coupon_id"]
    grand_total = total_cart_price + shipping_fee - discount_amount

    return render(
        request,
        "shop/cart_view.html",
        {
            "items": cart_items_data,
            "total": total_cart_price,
            "shipping_fee": shipping_fee,
            "grand_total": grand_total,
            "coupon_apply_form": coupon_apply_form,
            "coupon": coupon,
            "discount_amount": discount_amount,
            "cart": cart,
        },
    )


@require_POST
def apply_coupon(request):
    """Applies a coupon to the cart."""
    now = timezone.now()
    form = CouponApplyForm(request.POST)
    if form.is_valid():
        code = form.cleaned_data["code"]
        try:
            coupon = Coupon.objects.get(
                code__iexact=code,
                valid_from__lte=now,
                valid_to__gte=now,
                is_active=True,
            )

            # Check total usage limit
            if coupon.max_uses is not None and coupon.times_used >= coupon.max_uses:
                messages.error(request, _("This coupon has reached its usage limit."))
                return redirect("shop:cart_view")

            # Check per-user usage limit
            if request.user.is_authenticated:
                user_uses = Order.objects.filter(
                    user=request.user, coupon=coupon
                ).count()
                if user_uses >= coupon.max_uses_per_user:
                    messages.error(
                        request,
                        _(
                            "You have already used this coupon the maximum number of times."
                        ),
                    )
                    return redirect("shop:cart_view")

            request.session["coupon_id"] = coupon.id
            messages.success(request, _("Coupon applied successfully!"))
        except Coupon.DoesNotExist:
            request.session["coupon_id"] = None
            messages.error(request, _("This coupon is invalid or has expired."))
    return redirect("shop:cart_view")


@require_POST
def remove_coupon(request):
    """Removes an applied coupon from the session."""
    if "coupon_id" in request.session:
        del request.session["coupon_id"]
        messages.success(request, _("Coupon removed."))
    return redirect("shop:cart_view")


@require_POST
def update_cart_quantity(request):
    try:
        lang = getattr(request, "LANGUAGE_CODE", "en")  # Default to 'en' if not set
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            message = "Invalid JSON." if lang == "en" else "نص غير صالح."
            return JsonResponse(
                {"success": False, "message": message},
                status=HttpResponseBadRequest.status_code,
            )

        cart_item_id = data.get("cart_item_id")
        new_quantity = data.get("quantity")

        if not cart_item_id or new_quantity is None:
            message = (
                "Cart item ID or quantity not provided."
                if lang == "en"
                else "معرف عنصر السلة أو الكمية غير موجود."
            )
            return JsonResponse(
                {"success": False, "message": message},
                status=HttpResponseBadRequest.status_code,
            )

        try:
            cart_item_id = int(cart_item_id)
            new_quantity = int(new_quantity)
        except ValueError:
            message = (
                "Invalid quantity or item ID format."
                if lang == "en"
                else "تنسيق معرف العنصر أو الكمية غير صالح."
            )
            return JsonResponse(
                {"success": False, "message": message},
                status=HttpResponseBadRequest.status_code,
            )

        try:
            cart_item = get_object_or_404(
                CartItem.objects.select_related("cart", "product_variant"),
                id=cart_item_id,
            )
            if request.user.is_authenticated:
                if cart_item.cart.user != request.user:
                    message = (
                        "Unauthorized action." if lang == "en" else "إجراء غير مصرح به."
                    )
                    return JsonResponse(
                        {"success": False, "message": message},
                        status=HttpResponseForbidden.status_code,
                    )
            else:
                if cart_item.cart.session_key != request.session.session_key:
                    message = (
                        "Unauthorized action." if lang == "en" else "إجراء غير مصرح به."
                    )
                    return JsonResponse(
                        {"success": False, "message": message},
                        status=HttpResponseForbidden.status_code,
                    )

            if new_quantity <= 0:
                with transaction.atomic():
                    cart_item.delete()
                message = (
                    "Item removed from cart."
                    if lang == "en"
                    else "تمت إزالة العنصر من السلة."
                )
                status = "removed"
                item_total_price = Decimal("0.00")
            else:
                if cart_item.product_variant.stock_quantity < new_quantity:
                    new_quantity = cart_item.product_variant.stock_quantity
                with transaction.atomic():
                    cart_item.quantity = new_quantity
                    cart_item.save()
                message = (
                    "Cart quantity updated." if lang == "en" else "تم تحديث كمية السلة."
                )
                status = "updated"
                item_total_price = cart_item.get_total_price()

            request.session["cart_count"] = cart_item.cart.total_items
            return JsonResponse(
                {
                    "success": True,
                    "message": message,
                    "status": status,
                    "cart_item_id": cart_item_id,
                    "new_quantity": cart_item.quantity if status == "updated" else 0,
                    "item_total_price": str(item_total_price),
                    "cart_total_items": cart_item.cart.total_items,
                    "cart_total_price": str(cart_item.cart.total_price),
                }
            )

        except CartItem.DoesNotExist:
            message = (
                "Cart item not found."
                if lang == "en"
                else "لم يتم العثور على عنصر في السلة."
            )
            return JsonResponse({"success": False, "message": message}, status=404)

        except Exception as e:
            print(f"Error updating cart quantity: {e}")
            message = (
                f"An unexpected error occurred: {str(e)}"
                if lang == "en"
                else f"حدث خطأ غير متوقع: {str(e)}"
            )
            return JsonResponse({"success": False, "message": message}, status=500)

    except Exception as e:
        message = "An error occurred." if lang == "en" else "حدث خطأ."
        return JsonResponse({"success": False, "message": message}, status=500)


@transaction.atomic
def process_order(
    request, cart, shipping_form=None, payment_form=None, existing_address=None
):
    try:
        if not shipping_form and not existing_address:
            messages.error(request, _("Shipping information is required."))
            return redirect("shop:checkout")

        if not payment_form:
            messages.error(request, _("Payment information is required."))
            return redirect("shop:checkout")

        # Create order
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            full_name=(
                shipping_form.cleaned_data["full_name"]
                if shipping_form
                else existing_address.full_name
            ),
            email=(
                request.user.email if request.user.is_authenticated else ""
            ),  # Optional
            phone_number=(
                shipping_form.cleaned_data["phone_number"]
                if shipping_form
                else existing_address.phone_number
            ),
            subtotal=Decimal("0.00"),
            shipping_cost=Decimal(config.SHIPPING_RATE_CAIRO),  # Using your config
            grand_total=Decimal("0.00"),
            status="pending",
            payment_status="pending",
        )

        # Save shipping address
        if existing_address:
            shipping_address = existing_address
            shipping_address.order = order
            shipping_address.save()
        else:
            shipping_address = shipping_form.save(commit=False)
            if hasattr(shipping_address, "user") and request.user.is_authenticated:
                shipping_address.user = request.user
            shipping_address.order = order
            shipping_address.save()

        order.shipping_address = shipping_address
        order.save()

        # Create payment
        payment_data = payment_form.cleaned_data
        payment = Payment.objects.create(
            order=order,
            payment_method=payment_data.get("payment_method"),
            amount=Decimal("0.00"),  # Will update later
            transaction_id=f"TXN-{uuid.uuid4().hex[:10]}",
            is_success=False,
        )

        # Process cart items
        subtotal = Decimal("0.00")
        for cart_item in cart.items.select_related("product_variant").all():
            variant = cart_item.product_variant
            if variant.stock_quantity < cart_item.quantity:
                raise ValueError(
                    f"Not enough stock for {variant.product.name} "
                    f"({variant.color.name if variant.color else 'N/A'}, "
                    f"{variant.size.name if variant.size else 'N/A'}). "
                    f"Available: {variant.stock_quantity}, Requested: {cart_item.quantity}"
                )

            price = variant.get_price  # property
            OrderItem.objects.create(
                order=order,
                product_variant=variant,
                quantity=cart_item.quantity,
                price_at_purchase=price,
            )
            variant.stock_quantity -= cart_item.quantity
            variant.save()
            subtotal += price * cart_item.quantity

        # Update totals
        order.subtotal = subtotal
        order.grand_total = subtotal + order.shipping_cost
        order.save()

        # Update payment
        payment.amount = order.grand_total
        payment.is_success = True
        payment.save()

        # Finalize order
        order.status = "processing"
        order.payment_status = "paid"
        order.save()

        # Clear cart
        cart.items.all().delete()
        cart.update_totals()
        if not request.user.is_authenticated:
            cart.delete()
        request.session["cart_count"] = 0

        messages.success(
            request, _(f"Your order {order.order_number} has been placed successfully!")
        )
        return redirect("shop:order_confirmation", order_number=order.order_number)

    except ValueError as e:
        messages.error(request, _(f"Order failed: {e}"))
        return redirect("shop:checkout")
    except Exception as e:
        logger.exception(f"Order processing failed for user {request.user}: {e}")
        messages.error(request, _(f"An unexpected error occurred during checkout: {e}"))
        return redirect("shop:checkout")


def order_confirmation(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)

    if order.user != request.user and order.user is not None:
        return render(request, "shop/order_not_found.html", status=403)

    order_items = order.items.select_related(
        "product_variant__product", "product_variant__color", "product_variant__size"
    )

    return render(
        request,
        "shop/order_confirmation.html",
        {"order": order, "order_items": order_items},
    )


def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    is_vendor = False

    # Authorization check
    if request.user.is_authenticated:
        is_customer_of_order = order.user == request.user
        is_vendor_of_order = order.items.filter(
            product_variant__product__vendor__user=request.user
        ).exists()

        if not is_customer_of_order and not is_vendor_of_order:
            messages.error(request, _("You are not authorized to view this order."))
            return redirect("shop:home")
        if is_vendor_of_order:
            is_vendor = True
    elif order.user is not None:  # Anonymous order check
        messages.error(request, _("You must be logged in to view this order."))
        return redirect("shop:login")

    # Messaging logic
    message_form = MessageForm()
    if request.method == "POST":
        if not request.user.is_authenticated:
            return JsonResponse(
                {"success": False, "message": "Authentication required."}, status=403
            )

        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.order = order
            message.sender = request.user
            # Determine recipient
            if is_vendor:
                message.recipient = order.user
            else:  # Customer is sending
                # For simplicity, sending to the first vendor in the order.
                # A more complex system might allow choosing a vendor.
                first_item = order.items.first()
                if first_item and first_item.product_variant.product.vendor:
                    message.recipient = first_item.product_variant.product.vendor.user
                else:  # Should not happen in a valid order
                    messages.error(
                        request,
                        _("Could not determine the recipient for this message."),
                    )
                    return redirect(order.get_absolute_url())
            message.save()
            messages.success(request, _("Your message has been sent."))
            return redirect(order.get_absolute_url())

    order_items = order.items.select_related(
        "product_variant__product", "product_variant__color", "product_variant__size"
    ).all()
    messages_thread = order.messages.select_related("sender").order_by("created_at")

    return render(
        request,
        "shop/order_detail.html",
        {
            "order": order,
            "order_items": order_items,
            "messages": messages_thread,
            "message_form": message_form,
        },
    )


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    paginator = Paginator(orders, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "shop/order_history.html", {"orders": page_obj})


def get_available_sizes_ajax(request, product_id):
    """
    AJAX endpoint to get available sizes based on product and selected color.
    """
    if (
        request.method == "GET"
        and request.headers.get("x-requested-with") == "XMLHttpRequest"
    ):
        color_id = request.GET.get("color_id")
        try:
            # You should have a Product model with a method like get_available_sizes
            product = get_object_or_404(Product, id=product_id)
            available_sizes_query = product.get_available_sizes(color_id=color_id)

            # Convert queryset to a list of dictionaries for JSON response
            # Change 'available_sizes' to 'sizes' to match JavaScript
            available_sizes_data = list(available_sizes_query.values("id", "name"))

            return JsonResponse({"success": True, "sizes": available_sizes_data})
        except Product.DoesNotExist:
            return JsonResponse(
                {"success": False, "message": "Product not found."}, status=404
            )
    return JsonResponse({"success": False, "message": "Invalid request"}, status=400)


def vendor_detail(request, slug):
    # 1. Get the VendorProfile instance
    vendor_profile = get_object_or_404(VendorProfile, slug=slug)

    # 2. Access the related MnoryUser instance from the VendorProfile
    # As per your models.py, VendorProfile has a OneToOneField named 'user'
    # which points to settings.AUTH_USER_MODEL (your MnoryUser).
    vendor_user_instance = vendor_profile.user

    # Get products for this vendor, filtered by the VendorProfile instance
    products_queryset = Product.objects.filter(vendor=vendor_profile, is_active=True)

    # Apply filters
    price_min = request.GET.get("price_min")
    price_max = request.GET.get("price_max")
    category_id = request.GET.get("category")
    brand_id = request.GET.get("brand")
    colors_ids = request.GET.getlist(
        "colors"
    )  # request.GET.getlist returns a list of selected IDs
    sizes_ids = request.GET.getlist(
        "sizes"
    )  # request.GET.getlist returns a list of selected IDs
    sort_by = request.GET.get("sort", "-created_at")  # Default sort to newest first

    # Apply price filters
    if price_min:
        products_queryset = products_queryset.filter(price__gte=price_min)
    if price_max:
        products_queryset = products_queryset.filter(price__lte=price_max)

    # Apply category filter (accept either numeric id or slug)
    if category_id:
        if str(category_id).isdigit():
            products_queryset = products_queryset.filter(category_id=int(category_id))
        else:
            products_queryset = products_queryset.filter(category__slug=category_id)

    # Apply brand filter (accept either numeric id or slug)
    if brand_id:
        if str(brand_id).isdigit():
            products_queryset = products_queryset.filter(brand_id=int(brand_id))
        else:
            # support brand slug values (e.g., 'puma') or brand name
            products_queryset = products_queryset.filter(
                Q(brand__slug=brand_id) | Q(brand__name=brand_id)
            )

    # Apply colors filter (ManyToManyField through ProductColor)
    if colors_ids:
        # Filter products that have at least one of the selected colors through the ProductColor intermediate model
        products_queryset = products_queryset.filter(
            productcolor__color__id__in=colors_ids
        ).distinct()

    # Apply sizes filter (ManyToManyField through ProductSize)
    if sizes_ids:
        # Filter products that have at least one of the selected sizes through the ProductSize intermediate model
        products_queryset = products_queryset.filter(
            productsize__size__id__in=sizes_ids
        ).distinct()

    # Apply sorting
    products_queryset = products_queryset.order_by(sort_by)

    # Pagination
    paginator = Paginator(products_queryset, 9)  # Show 9 products per page
    page = request.GET.get("page")
    try:
        products_page = paginator.page(page)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)

    # Get filter options relevant to this vendor's active products
    # CORRECTED based on your models.py:
    # - Category and Brand use related_name='products' on Product model
    # - Color and Size use through models ProductColor and ProductSize respectively.

    # Filter Categories that have active products from this vendor
    categories = Category.objects.filter(
        products__vendor=vendor_profile, products__is_active=True
    ).distinct()

    # Filter Brands that have active products from this vendor
    brands = Brand.objects.filter(
        products__vendor=vendor_profile, products__is_active=True
    ).distinct()

    # Filter Colors that are associated with active products from this vendor via ProductColor
    colors = Color.objects.filter(
        productcolor__product__vendor=vendor_profile,
        productcolor__product__is_active=True,
    ).distinct()

    # Filter Sizes that are associated with active products from this vendor via ProductSize
    sizes = Size.objects.filter(
        productsize__product__vendor=vendor_profile,
        productsize__product__is_active=True,
    ).distinct()

    # Get min/max price for the vendor's products (for filter range)
    price_range = Product.objects.filter(
        vendor=vendor_profile, is_active=True
    ).aggregate(Min("price"), Max("price"))
    # Ensure price_range has a default if no products exist
    min_price_val = (
        price_range["price__min"] if price_range["price__min"] is not None else 0
    )
    max_price_val = (
        price_range["price__max"] if price_range["price__max"] is not None else 0
    )

    # Vendor stats
    vendor_stats = {
        "total_products": Product.objects.filter(
            vendor=vendor_profile, is_active=True
        ).count(),
        # Count categories that have active products from this vendor
        "categories_count": categories.count(),  # We already filtered `categories` above
    }

    # Related vendors: other vendors producing in the same categories
    related_qs = (
        VendorProfile.objects.filter(
            products__category__in=categories, products__is_active=True
        )
        .exclude(id=vendor_profile.id)
        .distinct()[:6]
    )

    # Ensure we have a safe vendor_location string for templates (some VendorProfile instances may not have `location`)
    vendor_location = getattr(vendor_profile, "location", "") or ""

    # Build a safe list of small dicts for related vendors to avoid missing attribute errors in templates
    related_vendors = []
    for rv in related_qs:
        # logo url if present
        logo_url = None
        try:
            if getattr(rv, "logo", None):
                logo_url = rv.logo.url
        except Exception:
            logo_url = None

        # safe location (use get_location_display if available)
        if hasattr(rv, "get_location_display"):
            try:
                safe_location = rv.get_location_display() or ""
            except Exception:
                safe_location = getattr(rv, "location", "") or ""
        else:
            safe_location = getattr(rv, "location", "") or ""

        related_vendors.append(
            {
                "slug": getattr(rv, "slug", ""),
                "store_name": getattr(rv, "store_name", ""),
                "logo_url": logo_url,
                "safe_location": safe_location,
            }
        )

    # Vendor reviews (if freelancing.Review exists) where the reviewee is the vendor's user
    vendor_reviews = []
    try:
        if vendor_user_instance:
            vendor_reviews = Review.objects.filter(
                reviewee=vendor_user_instance, is_public=True
            ).order_by("-created_at")[:5]
    except Exception:
        vendor_reviews = []

    context = {
        "vendor": vendor_profile,  # Pass the VendorProfile instance to the template
        "products": products_page,
        "categories": categories,
        "brands": brands,
        "colors": colors,
        "sizes": sizes,
        "price_range": {
            "price__min": min_price_val,
            "price__max": max_price_val,
        },  # Pass adjusted price_range
        "vendor_stats": vendor_stats,
        "related_vendors": related_vendors,
        "vendor_location": vendor_location,
        "vendor_reviews": vendor_reviews,
    }
    return render(request, "shop/vendor_detail.html", context)


# --- Advertisement Tracking Views ---
@require_POST
def track_ad_view(request):
    """Track advertisement view count via AJAX."""
    try:
        import json
        from .models import Advertisement

        data = json.loads(request.body)
        ad_id = data.get("ad_id")

        if not ad_id:
            return JsonResponse({"error": "Ad ID required"}, status=400)

        ad = Advertisement.objects.filter(id=ad_id, is_active=True).first()
        if not ad:
            return JsonResponse({"error": "Advertisement not found"}, status=404)

        # Increment view count
        ad.increment_view_count()

        # Refresh from database to get actual count
        ad.refresh_from_db()

        return JsonResponse({"success": True, "view_count": ad.view_count})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def profile_view(request):
    recent_orders = Order.objects.filter(user=request.user).order_by("-created_at")[:5]
    context = {"recent_orders": recent_orders}
    return render(request, "accounts/profile.html", context)


@login_required
def edit_profile(request):
    if request.method == "POST":
        form = UserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Profile updated successfully!"))
            return redirect("shop:profile")
    else:
        form = UserChangeForm(instance=request.user)
    return render(request, "accounts/edit_profile.html", {"form": form})


@login_required
def address_list(request):
    addresses = ShippingAddress.objects.filter(user=request.user)
    return render(request, "accounts/address_list.html", {"addresses": addresses})


@login_required
def address_add(request):
    if request.method == "POST":
        form = ShippingAddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, _("Address added successfully!"))
            return redirect("shop:address_list")
    else:
        form = ShippingAddressForm()
    return render(request, "accounts/address_form.html", {"form": form})


@login_required
def address_edit(request, address_id):
    address = get_object_or_404(ShippingAddress, id=address_id, user=request.user)
    if request.method == "POST":
        form = ShippingAddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, _("Address updated successfully!"))
            return redirect("shop:address_list")
    else:
        form = ShippingAddressForm(instance=address)
    return render(request, "accounts/address_form.html", {"form": form})


@login_required
@require_POST
def address_delete(request, address_id):
    address = get_object_or_404(ShippingAddress, id=address_id, user=request.user)
    address.delete()
    messages.success(request, _("Address deleted successfully!"))
    return redirect("shop:address_list")


@login_required
def account_settings(request):
    from django.contrib.auth.forms import PasswordChangeForm
    from django.contrib.auth import update_session_auth_hash

    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, _("Your password was successfully updated!"))
            return redirect("shop:account_settings")
        else:
            messages.error(request, _("Please correct the error below."))
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "accounts/account_settings.html", {"form": form})


@login_required
def vendor_dashboard(request):
    if not request.user.is_vendor_type:
        # from django.contrib import messages
        messages.error(request, _("Access denied. This page is for vendors only."))
        return redirect("shop:home")

    vendor_profile = get_object_or_404(VendorProfile, user=request.user)

    # --- Date Filtering ---
    period = request.GET.get("period", "7d")
    end_date = timezone.now()
    if period == "30d":
        start_date = end_date - timedelta(days=29)
        period_label = _("Last 30 Days")
    elif period == "month":
        start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        period_label = _("This Month")
    else:  # Default to 7 days
        period = "7d"
        start_date = end_date - timedelta(days=6)
        period_label = _("Last 7 Days")

    # --- Base Querysets for the selected period ---
    total_products = Product.objects.filter(vendor=vendor_profile).count()
    vendor_order_items = OrderItem.objects.filter(
        product_variant__product__vendor=vendor_profile
    )
    total_sales = (
        vendor_order_items.aggregate(total=Sum("price_at_purchase"))["total"] or 0
    )
    vendor_order_items_period = vendor_order_items.filter(
        order__created_at__range=(start_date, end_date)
    )
    recent_orders = (
        Order.objects.filter(items__in=vendor_order_items)
        .distinct()
        .order_by("-created_at")[:5]
    )

    # Top Selling Products
    # --- KPIs for the selected period ---
    total_sales_period = (
        vendor_order_items_period.aggregate(
            total=Sum(F("price_at_purchase") * F("quantity"))
        )["total"]
        or 0
    )
    total_orders_period = Order.objects.filter(
        items__in=vendor_order_items_period
    ).distinct()
    total_orders_count_period = total_orders_period.count()
    average_order_value = (
        total_sales_period / total_orders_count_period
        if total_orders_count_period > 0
        else 0
    )
    unique_customers_count = total_orders_period.values("email").distinct().count()

    # --- Fetch financial data from VendorOrder records ---
    vendor_orders_period = VendorOrder.objects.filter(
        vendor=vendor_profile, created_at__range=(start_date, end_date)
    )
    financial_summary = vendor_orders_period.aggregate(
        total_shipping=Sum("shipping_charged"),
        total_commission=Sum("commission_amount"),
        total_payout=Sum("net_payout"),
    )

    # --- Shipping & Net Revenue Calculation ---
    total_shipping_revenue = Decimal("0.00")
    try:
        vendor_shipping_settings = VendorShipping.objects.get(vendor=vendor_profile)
        for order in total_orders_period:
            # Calculate the subtotal of this vendor's items within this specific order
            vendor_subtotal_in_order = order.items.filter(
                product_variant__product__vendor=vendor_profile
            ).aggregate(subtotal=Sum(F("price_at_purchase") * F("quantity")))[
                "subtotal"
            ] or Decimal(
                "0.00"
            )

            # Check if this vendor's items qualify for their free shipping
            if not (
                vendor_shipping_settings.free_shipping_threshold
                and vendor_subtotal_in_order
                >= vendor_shipping_settings.free_shipping_threshold
            ):
                city = (
                    order.shipping_address.city
                    if order.shipping_address
                    else "INSIDE_CAIRO"
                )
                if city == "OUTSIDE_CAIRO":
                    total_shipping_revenue += (
                        vendor_shipping_settings.shipping_rate_outside_cairo
                    )
                else:
                    total_shipping_revenue += (
                        vendor_shipping_settings.shipping_rate_cairo
                    )
    except VendorShipping.DoesNotExist:
        # If for some reason shipping settings don't exist, shipping revenue is 0
        total_shipping_revenue = Decimal("0.00")

    # Use the new aggregated values for accuracy
    total_shipping_revenue = financial_summary["total_shipping"] or Decimal("0.00")
    total_commission = financial_summary["total_commission"] or Decimal("0.00")
    net_payout = financial_summary["total_payout"] or Decimal("0.00")

    # --- Payouts Data ---
    payout_history = vendor_profile.payouts.all()[:10]  # Get last 10 payouts
    payout_form = PayoutRequestForm(vendor_profile=vendor_profile)

    # --- Data for Tables ---
    recent_orders_list = (
        Order.objects.filter(items__in=vendor_order_items)
        .distinct()
        .order_by("-created_at")[:5]
    )
    top_products_period = (
        Product.objects.filter(vendor=vendor_profile, is_active=True)
        .annotate(
            total_sold=Sum(
                "variants__orderitem__quantity",
                filter=Q(
                    variants__orderitem__order__created_at__range=(start_date, end_date)
                ),
            ),
            total_revenue=Sum(
                F("variants__orderitem__quantity")
                * F("variants__orderitem__price_at_purchase"),
                filter=Q(
                    variants__orderitem__order__created_at__range=(start_date, end_date)
                ),
            ),
        )
        .filter(total_sold__gt=0)
        .order_by("-total_sold")[:5]
    )
    # Chart Data: Sales for the last 7 days
    # Get recent product reviews
    recent_reviews_list = (
        Review.objects.filter(product__vendor=vendor_profile)
        .select_related("reviewer", "product")
        .order_by("-created_at")[:5]
    )

    # --- Notifications ---
    notifications = request.user.shop_notifications.all()[:10]
    unread_notifications_count = request.user.shop_notifications.filter(
        is_read=False,
    ).count()

    # --- Chart Data ---
    # 1. Daily Sales for Line Chart (Last 7/30 days)
    daily_sales_data = (
        vendor_order_items_period.annotate(day=TruncDay("order__created_at"))
        .values("day")
        .annotate(daily_sales=Sum(F("price_at_purchase") * F("quantity")))
        .order_by("day")
    )
    days_in_period = (end_date.date() - start_date.date()).days + 1
    chart_labels = [
        (start_date + timedelta(days=i)).strftime("%b %d")
        for i in range(days_in_period)
    ]
    chart_sales = [0.0] * days_in_period
    sales_dict = {
        item["day"].strftime("%b %d"): float(item["daily_sales"])
        for item in daily_sales_data
    }
    for i, label in enumerate(chart_labels):
        chart_sales[i] = sales_dict.get(label, 0.0)

    # 2. Sales by Category for Pie Chart
    category_sales_data = (
        vendor_order_items_period.values("product_variant__product__category__name")
        .annotate(total=Sum(F("price_at_purchase") * F("quantity")))
        .order_by("-total")
    )
    category_chart_labels = [
        item["product_variant__product__category__name"] for item in category_sales_data
    ]
    category_chart_sales = [float(item["total"]) for item in category_sales_data]

    # 3. Monthly Sales for Bar Chart (Last 12 months)
    twelve_months_ago = end_date.replace(year=end_date.year - 1)
    monthly_sales_data = (
        vendor_order_items.filter(order__created_at__gte=twelve_months_ago)
        .annotate(day=TruncDay("order__created_at"))
        .values("day")
        .annotate(monthly_sales=Sum(F("price_at_purchase") * F("quantity")))
        .order_by("day")
    )

    context = {
        "vendor_profile": vendor_profile,
        "period": period,
        "period_label": period_label,
        "total_products": total_products,
        "total_sales": total_sales_period,
        "total_orders_count": total_orders_count_period,
        "average_order_value": average_order_value,
        "unique_customers_count": unique_customers_count,
        "total_shipping_revenue": total_shipping_revenue,
        "total_commission": total_commission,
        "net_payout": net_payout,
        "payout_history": payout_history,
        "payout_form": payout_form,
        "recent_orders": recent_orders_list,
        "recent_reviews": recent_reviews_list,
        "top_products": top_products_period,
        "chart_labels": json.dumps(chart_labels),
        "chart_sales_data": json.dumps(chart_sales),
        "category_chart_labels": json.dumps(category_chart_labels),
        "category_chart_sales": json.dumps(category_chart_sales),
        "notifications": notifications,
        "unread_notifications_count": unread_notifications_count,
    }
    return render(request, "shop/vendor_dashboard.html", context)


@login_required
def vendor_manage_orders(request):
    """
    Dedicated page for vendors to view, search, and filter their orders.
    """
    if not request.user.is_vendor_type:
        messages.error(request, _("Access denied. This page is for vendors only."))
        return redirect("shop:home")

    vendor_profile = get_object_or_404(VendorProfile, user=request.user)

    # Get all order items belonging to this vendor
    vendor_order_items = OrderItem.objects.filter(
        product_variant__product__vendor=vendor_profile
    ).select_related("order")

    # Get the unique order IDs
    order_ids = vendor_order_items.values_list("order_id", flat=True).distinct()

    # Base queryset for orders
    order_list = Order.objects.filter(id__in=order_ids).order_by("-created_at")

    # Search and Filter
    search_query = request.GET.get("q", "")
    status_filter = request.GET.get("status", "")

    if search_query:
        order_list = order_list.filter(
            Q(order_number__icontains=search_query)
            | Q(full_name__icontains=search_query)
            | Q(email__icontains=search_query)
        )

    if status_filter:
        order_list = order_list.filter(status=status_filter)

    # Annotate each order with the total value of the vendor's items in that order
    order_list = order_list.annotate(
        vendor_total=Sum(
            "items__price_at_purchase",
            filter=Q(items__product_variant__product__vendor=vendor_profile),
        )
    )

    paginator = Paginator(order_list, 15)  # 15 orders per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "orders": page_obj,
        "vendor_profile": vendor_profile,
        "search_query": search_query,
        "status_filter": status_filter,
        "status_choices": Order.STATUS_CHOICES,
    }
    return render(request, "shop/vendor_manage_orders.html", context)


@login_required
def vendor_manage_products(request):
    if not request.user.is_vendor_type:
        messages.error(request, _("Access denied. This page is for vendors only."))
        return redirect("shop:home")

    vendor_profile = get_object_or_404(VendorProfile, user=request.user)

    if request.method == "POST":
        bulk_form = ProductBulkEditForm(request.POST)
        bulk_form.fields["product_ids"].queryset = Product.objects.filter(
            vendor=vendor_profile
        )
        if bulk_form.is_valid():
            product_ids = bulk_form.cleaned_data["product_ids"]
            update_data = {}
            if bulk_form.cleaned_data.get("category"):
                update_data["category"] = bulk_form.cleaned_data["category"]
            if bulk_form.cleaned_data.get("brand"):
                update_data["brand"] = bulk_form.cleaned_data["brand"]
            if bulk_form.cleaned_data.get("price") is not None:
                update_data["price"] = bulk_form.cleaned_data["price"]
            if bulk_form.cleaned_data.get("sale_price") is not None:
                update_data["sale_price"] = bulk_form.cleaned_data["sale_price"]
            if bulk_form.cleaned_data.get("is_active"):
                update_data["is_active"] = bulk_form.cleaned_data["is_active"] == "true"

            if update_data:
                with transaction.atomic():
                    updated_count = product_ids.update(**update_data)
                messages.success(
                    request,
                    _(f"{updated_count} products have been updated successfully."),
                )
            else:
                messages.warning(
                    request, _("No changes were selected for bulk editing.")
                )
            return redirect("shop:vendor_manage_products")

    vendor_profile = get_object_or_404(VendorProfile, user=request.user)
    products_list = Product.objects.filter(vendor=vendor_profile).order_by(
        "-created_at"
    )

    # Search and Filter
    search_query = request.GET.get("q", "")
    status_filter = request.GET.get("status", "")

    if search_query:
        products_list = products_list.filter(
            Q(name__icontains=search_query) | Q(sku__icontains=search_query)
        )

    if status_filter:
        products_list = products_list.filter(is_active=(status_filter == "active"))

    paginator = Paginator(products_list, 10)  # 10 products per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    bulk_edit_form = ProductBulkEditForm()
    bulk_edit_form.fields["product_ids"].queryset = Product.objects.filter(
        vendor=vendor_profile
    )

    context = {
        "products": page_obj,
        "vendor_profile": vendor_profile,
        "search_query": search_query,
        "status_filter": status_filter,
        "bulk_edit_form": bulk_edit_form,
    }
    return render(request, "shop/vendor_manage_products.html", context)


@login_required
def vendor_add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.vendor = request.user.vendorprofile
            product.save()
            form.save_m2m()  # For many-to-many fields if any
            messages.success(request, _("Product added successfully!"))
            return redirect("shop:vendor_manage_products")
    else:
        form = ProductForm()
    context = {"form": form, "title": _("Add New Product")}
    return render(request, "shop/vendor_product_form.html", context)


@login_required
def vendor_edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    # Ensure the product belongs to the logged-in vendor
    if product.vendor != request.user.vendorprofile:
        messages.error(request, _("You do not have permission to edit this product."))
        return redirect("shop:vendor_manage_products")

    if request.method == "POST":
        product_form = ProductForm(
            request.POST, request.FILES, instance=product, prefix="product"
        )
        image_formset = ProductImageFormSet(
            request.POST, request.FILES, instance=product, prefix="images"
        )
        variant_formset = ProductVariantFormSet(
            request.POST, request.FILES, instance=product, prefix="variants"
        )

        if (
            product_form.is_valid()
            and variant_formset.is_valid()  # noqa
            and image_formset.is_valid()
        ):
            product_form.save()
            variants = variant_formset.save(commit=False)

            # Save images before variants
            images = image_formset.save(commit=False)
            for image in images:
                image.product = product
                image.save()
            for form in image_formset.deleted_forms:
                if form.instance.pk:
                    form.instance.delete()

            for variant in variants:
                variant.product = product
                variant.save()

            for form in variant_formset.deleted_forms:
                if form.instance.pk:
                    form.instance.delete()

            # Recalculate total stock for the main product
            total_stock = (
                product.variants.aggregate(total=Sum("stock_quantity"))["total"] or 0
            )
            product.stock_quantity = total_stock
            product.save(update_fields=["stock_quantity"])

            # Automatically set the first image as main if none is selected
            product.refresh_from_db()
            if (
                product.images.exists()
                and not product.images.filter(is_main=True).exists()
            ):
                first_image = product.images.order_by("order").first()
                if first_image:
                    first_image.is_main = True
                    first_image.save(update_fields=["is_main"])

            messages.success(request, _("Product updated successfully!"))
            return redirect("shop:vendor_manage_products")
    else:
        product_form = ProductForm(instance=product, prefix="product")
        image_formset = ProductImageFormSet(instance=product, prefix="images")
        variant_formset = ProductVariantFormSet(instance=product, prefix="variants")

    context = {
        "form": product_form,
        "image_formset": image_formset,
        "variant_formset": variant_formset,
        "title": _("Edit Product"),
    }
    return render(request, "shop/vendor_product_form.html", context)


@login_required
def vendor_bulk_stock_edit(request):
    """
    A dedicated page for vendors to bulk-edit stock quantities of their product variants.
    """
    if not request.user.is_vendor_type:
        messages.error(request, _("Access denied. This page is for vendors only."))
        return redirect("shop:home")

    vendor_profile = get_object_or_404(VendorProfile, user=request.user)

    if request.method == "POST":
        with transaction.atomic():
            updated_count = 0
            for key, value in request.POST.items():
                if key.startswith("stock-"):
                    try:
                        variant_id = int(key.split("-")[1])
                        stock_quantity = int(value)

                        # Security check: ensure the variant belongs to the vendor
                        variant = ProductVariant.objects.select_for_update().get(
                            id=variant_id, product__vendor=vendor_profile
                        )

                        if variant.stock_quantity != stock_quantity:
                            variant.stock_quantity = stock_quantity
                            variant.is_available = stock_quantity > 0
                            variant.save(
                                update_fields=["stock_quantity", "is_available"]
                            )
                            updated_count += 1

                    except (ValueError, IndexError, ProductVariant.DoesNotExist):
                        # Ignore invalid data, but log it
                        logger.warning(
                            f"Bulk stock update received invalid data: {key}={value}"
                        )
                        continue

            # Recalculate total stock for all affected products
            affected_product_ids = (
                ProductVariant.objects.filter(product__vendor=vendor_profile)
                .values_list("product_id", flat=True)
                .distinct()
            )
            for product_id in affected_product_ids:
                product = Product.objects.get(id=product_id)
                total_stock = (
                    product.variants.aggregate(total=Sum("stock_quantity"))["total"]
                    or 0
                )
                product.stock_quantity = total_stock
                product.save(update_fields=["stock_quantity"])

        messages.success(
            request,
            _(f"{updated_count} variant stock quantities updated successfully."),
        )
        return redirect("shop:vendor_bulk_stock_edit")

    # GET request logic
    variants_list = (
        ProductVariant.objects.filter(product__vendor=vendor_profile)
        .select_related("product", "color", "size")
        .order_by("product__name", "color__name", "size__order")
    )

    # Filtering
    search_query = request.GET.get("q", "")
    if search_query:
        variants_list = variants_list.filter(
            Q(product__name__icontains=search_query) | Q(sku__icontains=search_query)
        )

    paginator = Paginator(variants_list, 25)  # 25 variants per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "variants": page_obj,
        "vendor_profile": vendor_profile,
        "search_query": search_query,
    }

    return render(request, "shop/vendor_bulk_stock_edit.html", context)


@login_required
@require_POST
def vendor_mark_notifications_as_read(request):
    """AJAX endpoint for vendors to mark their notifications as read."""
    if not request.user.is_vendor_type:
        return JsonResponse(
            {"success": False, "message": _("Access denied.")}, status=403
        )

    try:
        updated_count = request.user.notifications.filter(is_read=False).update(
            is_read=True
        )
        return JsonResponse({"success": True, "updated_count": updated_count})
    except Exception as e:
        logger.error(
            f"Error marking notifications as read for user {request.user.email}: {e}"
        )
        return JsonResponse(
            {"success": False, "message": _("An error occurred.")}, status=500
        )


@login_required
def vendor_export_sales_csv(request):
    """
    Exports a vendor's sales data for a given period as a CSV file.
    """
    if not request.user.is_vendor_type:
        return HttpResponseForbidden("Access denied.")

    vendor_profile = get_object_or_404(VendorProfile, user=request.user)

    # --- Date Filtering (same logic as dashboard) ---
    period = request.GET.get("period", "7d")
    end_date = timezone.now()
    if period == "30d":
        start_date = end_date - timedelta(days=29)
    elif period == "month":
        start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = end_date - timedelta(days=6)

    # Fetch order items for the period
    sales_items = (
        OrderItem.objects.filter(
            product_variant__product__vendor=vendor_profile,
            order__payment_status="paid",
            order__created_at__range=(start_date, end_date),
        )
        .select_related(
            "order",
            "product_variant__product",
            "product_variant__color",
            "product_variant__size",
        )
        .order_by("-order__created_at")
    )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="sales_report_{vendor_profile.slug}_{start_date.date()}_to_{end_date.date()}.csv"'
    )

    writer = csv.writer(response)
    # Write CSV header
    writer.writerow(
        [
            "Order Number",
            "Order Date",
            "Product Name",
            "Variant (Color/Size)",
            "Quantity",
            "Price per Item (EGP)",
            "Total Price (EGP)",
        ]
    )

    # Write data rows
    for item in sales_items:
        variant_str = (
            f"{item.product_variant.color.name} / {item.product_variant.size.name}"
        )
        writer.writerow(
            [
                item.order.order_number,
                item.order.created_at.strftime("%Y-%m-%d %H:%M"),
                item.product_variant.product.name,
                variant_str,
                item.quantity,
                item.price_at_purchase,
                item.get_total_price(),
            ]
        )

    return response


@login_required
@require_POST
def vendor_reply_to_review(request, review_id):
    if not request.user.is_vendor_type:
        return JsonResponse(
            {"success": False, "message": _("Access denied.")}, status=403
        )

    review = get_object_or_404(Review, id=review_id)

    # Security check: ensure the product belongs to the current vendor
    if review.product.vendor != request.user.vendorprofile:
        return JsonResponse(
            {
                "success": False,
                "message": _("You do not have permission to reply to this review."),
            },
            status=403,
        )

    form = ReviewReplyForm(request.POST, instance=review)
    if form.is_valid():
        reply = form.save(commit=False)
        reply.replied_at = timezone.now()
        reply.save()
        return JsonResponse(
            {
                "success": True,
                "reply_text": reply.reply,
                "replied_at": timezone.localtime(reply.replied_at).strftime(
                    "%b %d, %Y"
                ),
            }
        )
    else:
        return JsonResponse({"success": False, "errors": form.errors}, status=400)


@login_required
@require_POST
def vendor_delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    # Ensure the product belongs to the logged-in vendor
    if product.vendor != request.user.vendorprofile:
        return JsonResponse(
            {
                "success": False,
                "message": _("You do not have permission to delete this product."),
            },
            status=403,
        )

    try:
        product.delete()
        return JsonResponse(
            {"success": True, "message": _("Product deleted successfully.")}
        )
    except Exception as e:
        logger.error(
            f"Error deleting product {product_id} by user {request.user.email}: {e}"
        )
        return JsonResponse(
            {
                "success": False,
                "message": _("An error occurred while deleting the product."),
            },
            status=500,
        )


@login_required
def vendor_manage_reviews(request):
    if not request.user.is_vendor_type:
        messages.error(request, _("Access denied. This page is for vendors only."))
        return redirect("shop:home")

    vendor_profile = get_object_or_404(VendorProfile, user=request.user)

    review_list = (
        Review.objects.filter(product__vendor=vendor_profile)
        .select_related("user", "product")
        .order_by("-created_at")
    )

    # Search and Filter
    search_query = request.GET.get("q", "")
    rating_filter = request.GET.get("rating", "")

    if search_query:
        review_list = review_list.filter(
            Q(product__name__icontains=search_query)
            | Q(user__email__icontains=search_query)
            | Q(comment__icontains=search_query)
        )

    if rating_filter:
        review_list = review_list.filter(rating=rating_filter)

    paginator = Paginator(review_list, 10)  # 10 reviews per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "reviews": page_obj,
        "search_query": search_query,
        "rating_filter": rating_filter,
    }
    return render(request, "shop/vendor_manage_reviews.html", context)


@require_POST
def track_ad_click(request):
    """Track advertisement click count via AJAX."""
    try:
        data = json.loads(request.body)
        ad_id = data.get("ad_id")

        if not ad_id:
            return JsonResponse({"error": "Ad ID required"}, status=400)

        ad = Advertisement.objects.filter(id=ad_id, is_active=True).first()
        if not ad:
            return JsonResponse({"error": "Advertisement not found"}, status=404)

        # Increment click count
        ad.increment_click_count()

        # Refresh from database to get actual count
        ad.refresh_from_db()

        return JsonResponse({"success": True, "click_count": ad.click_count})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def search_products(request):
    """Search for products via AJAX."""
    try:
        query = request.GET.get("q", "").strip()

        if not query:
            return JsonResponse({"products": []})

        products = (
            Product.objects.filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(brand__name__icontains=query)
                | Q(category__name__icontains=query),
                is_active=True,
                is_available=True,
            )
            .select_related("category", "subcategory", "brand")
            .prefetch_related("images")[:10]
        )

        results = []
        for product in products:
            main_image = product.get_main_image()
            results.append(
                {
                    "id": product.id,
                    "name": product.name,
                    "price": str(product.get_price()),
                    "url": product.get_absolute_url(),
                    "image": (
                        main_image.image.url if main_image and main_image.image else ""
                    ),
                    "category": product.category.name if product.category else "",
                    "brand": product.brand.name if product.brand else "",
                }
            )

        return JsonResponse({"products": results})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_product_variants(request, product_id):
    """
    AJAX endpoint to get product variants based on color and size filters.
    Returns a list of matching variants with stock info.
    """
    try:
        product = get_object_or_404(Product, id=product_id)
    except ValueError:
        return JsonResponse(
            {"variants": [], "message": _("Invalid product ID.")}, status=400
        )

    color_id = request.GET.get("color")
    size_id = request.GET.get("size")

    variants_queryset = ProductVariant.objects.filter(
        product=product,
        is_available=True,
        stock_quantity__gt=0,  # Only show variants that are in stock
    ).select_related(
        "color", "size"
    )  # Efficiently fetch related color and size objects

    if color_id:
        try:
            variants_queryset = variants_queryset.filter(color__id=int(color_id))
        except (ValueError, TypeError):
            # If color_id is invalid, return empty results (or all if that's desired behavior)
            return JsonResponse(
                {"variants": [], "message": _("Invalid color ID.")}, status=400
            )

    if size_id:
        try:
            variants_queryset = variants_queryset.filter(size__id=int(size_id))
        except (ValueError, TypeError):
            # If size_id is invalid, return empty results
            return JsonResponse(
                {"variants": [], "message": _("Invalid size ID.")}, status=400
            )

    results = []
    for variant in variants_queryset:
        results.append(
            {
                "id": variant.id,
                "color_id": variant.color.id if variant.color else None,
                "color_name": variant.color.name if variant.color else _("N/A"),
                "size_id": variant.size.id if variant.size else None,
                "size_name": variant.size.name if variant.size else _("N/A"),
                "price": str(
                    variant.get_price()
                ),  # Ensure Decimal is serialized as string
                "stock": variant.stock_quantity,
                "sku": variant.sku,
            }
        )

    return JsonResponse({"variants": results})


@require_GET
def get_cart_and_wishlist_counts(request):
    """
    Returns JSON with counts of items in cart and wishlist.
    Supports logged-in users and anonymous users (session).
    """
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        cart_count = cart.total_items if cart else 0
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.save()
            session_key = request.session.session_key
        cart = Cart.objects.filter(session_key=session_key).first()
        cart_count = cart.total_items if cart else 0

    if request.user.is_authenticated:
        wishlist = Wishlist.objects.filter(user=request.user).first()
        wishlist_count = wishlist.items.count() if wishlist else 0
    else:
        wishlist_session = request.session.get("wishlist", [])
        wishlist_count = len(wishlist_session)

    return JsonResponse(
        {
            "success": True,
            "cart_count": cart_count,
            "wishlist_count": wishlist_count,
        }
    )


# --- Wishlist Views ---
def wishlist_view(request):
    """Displays the user's wishlist with pagination."""
    products_qs = Product.objects.none()
    products_in_wishlist_ids = set()
    if request.user.is_authenticated:
        try:
            wishlist = request.user.wishlist
            products_qs = (
                Product.objects.filter(wishlistitem__wishlist=wishlist)
                .select_related("category", "subcategory", "brand")
                .prefetch_related("images", "variants__color", "variants__size")
                .order_by("name")
            )
            products_in_wishlist_ids = set(
                wishlist.items.values_list("product_id", flat=True)
            )
        except Wishlist.DoesNotExist:
            products_qs = Product.objects.none()
            products_in_wishlist_ids = set()
    else:
        wishlist_session = request.session.get("wishlist", [])
        if wishlist_session:
            products_qs = (
                Product.objects.filter(id__in=wishlist_session)
                .select_related("category", "subcategory", "brand")
                .prefetch_related("images")
                .order_by("name")
            )
            products_in_wishlist_ids = set(wishlist_session)
        else:
            products_qs = Product.objects.none()
            products_in_wishlist_ids = set()

    # Pagination: 8 products per page
    paginator = Paginator(products_qs, 8)
    page = request.GET.get("page", 1)
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    # Update wishlist count in session
    request.session["wishlist_count"] = products_qs.count()

    context = {
        "products": products,
        "products_in_wishlist_ids": products_in_wishlist_ids,
    }
    return render(request, "shop/wishlist_view.html", context)


@require_POST
def add_to_cart(request):
    # Determine current language
    lang = getattr(request, "LANGUAGE_CODE", "en")

    try:
        if request.content_type and request.content_type.startswith("application/json"):
            try:
                data = json.loads(request.body)
            except Exception:
                data = {}
        else:
            data = request.POST
        product_variant_id = data.get("product_variant_id")
        product_id = data.get("product_id")
        color_id = data.get("color_id")
        size_id = data.get("size_id")
        try:
            quantity = int(data.get("quantity", 1))
        except (ValueError, TypeError):
            quantity = 1
    except Exception:
        message = "Invalid data provided." if lang == "en" else "بيانات غير صالحة."
        return JsonResponse({"success": False, "message": message}, status=400)

    product_variant = None
    product = None

    # If color and size are provided, find the variant
    if color_id and size_id and product_id:
        try:
            product = Product.objects.get(
                id=product_id, is_active=True, is_available=True
            )
            product_variant = ProductVariant.objects.filter(
                product=product,
                color_id=color_id,
                size_id=size_id,
                is_available=True,
                stock_quantity__gt=0,
            ).first()

            if not product_variant:
                message = (
                    "This color and size combination is not available."
                    if lang == "en"
                    else "هذا المزيج من اللون والحجم غير متاح."
                )
                return JsonResponse({"success": False, "message": message}, status=400)
        except Product.DoesNotExist:
            message = (
                "Product not found or not available."
                if lang == "en"
                else "المنتج غير موجود أو غير متوفر."
            )
            return JsonResponse({"success": False, "message": message}, status=404)
    elif product_variant_id:
        try:
            product_variant = ProductVariant.objects.get(
                id=product_variant_id, is_available=True
            )
            product = product_variant.product
        except ProductVariant.DoesNotExist:
            message = (
                "Product variant not found or not available."
                if lang == "en"
                else "النسخة المحددة من المنتج غير موجودة أو غير متوفرة."
            )
            return JsonResponse({"success": False, "message": message}, status=404)
    elif product_id:
        try:
            product = Product.objects.get(
                id=product_id, is_active=True, is_available=True
            )
            product_variant = (
                ProductVariant.objects.filter(
                    product=product, is_available=True, stock_quantity__gt=0
                )
                .order_by("pk")
                .first()
            )
            if not product_variant:
                message = (
                    f"No available variants for {product.name} or out of stock."
                    if lang == "en"
                    else f"لا توجد نسخ متاحة لـ {product.name} أو نفدت الكمية."
                )
                return JsonResponse({"success": False, "message": message}, status=400)
        except Product.DoesNotExist:
            message = (
                "Product not found or not available."
                if lang == "en"
                else "المنتج غير موجود أو غير متوفر."
            )
            return JsonResponse({"success": False, "message": message}, status=404)
    else:
        message = (
            "Product or variant not provided."
            if lang == "en"
            else "لم يتم تقديم منتج أو نسخة."
        )
        return JsonResponse({"success": False, "message": message}, status=400)

    if quantity <= 0:
        message = (
            "Quantity must be at least 1."
            if lang == "en"
            else "يجب أن تكون الكمية على الأقل 1."
        )
        return JsonResponse({"success": False, "message": message}, status=400)

    if product_variant.stock_quantity < quantity:
        message = (
            (
                f'Not enough stock for {product.name} ({product_variant.color.name if product_variant.color else "N/A"}, '
                f'{product_variant.size.name if product_variant.size else "N/A"}). Available: {product_variant.stock_quantity}.'
            )
            if lang == "en"
            else (
                f'الكمية غير كافية للمنتج {product.name} ({product_variant.color.name if product_variant.color else "غير متوفر"}, '
                f'{product_variant.size.name if product_variant.size else "غير متوفر"}). المتوفر: {product_variant.stock_quantity}.'
            )
        )
        return JsonResponse({"success": False, "message": message}, status=400)

    with transaction.atomic():
        if request.user.is_authenticated:
            cart, created = Cart.objects.select_for_update().get_or_create(
                user=request.user
            )
        else:
            session_key = request.session.session_key
            if not session_key:
                request.session.save()
                session_key = request.session.session_key
            cart, created = Cart.objects.select_for_update().get_or_create(
                session_key=session_key
            )

        cart_item, created = CartItem.objects.select_for_update().get_or_create(
            cart=cart, product_variant=product_variant, defaults={"quantity": quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        request.session["cart_count"] = cart.total_items
        message = (
            "Item added to cart successfully!"
            if lang == "en"
            else "تمت إضافة العنصر إلى السلة بنجاح!"
        )
        return JsonResponse(
            {"success": True, "message": message, "cart_total_items": cart.total_items}
        )


@require_POST
def add_to_wishlist(request):
    lang = getattr(request, "LANGUAGE_CODE", "en")
    try:
        if request.content_type and request.content_type.startswith("application/json"):
            try:
                data = json.loads(request.body)
            except Exception:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Invalid JSON." if lang == "en" else "نص غير صالح.",
                    },
                    status=400,
                )
        else:
            data = request.POST
        product_id = data.get("product_id")
        if not product_id:
            return JsonResponse(
                {
                    "success": False,
                    "message": (
                        "Product ID not provided."
                        if lang == "en"
                        else "معرف المنتج غير موجود."
                    ),
                },
                status=400,
            )
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return JsonResponse(
                {
                    "success": False,
                    "message": (
                        "Product not found." if lang == "en" else "المنتج غير موجود."
                    ),
                },
                status=404,
            )

        if request.user.is_authenticated:
            with transaction.atomic():
                wishlist, created = Wishlist.objects.select_for_update().get_or_create(
                    user=request.user
                )
                wishlist_item, item_created = WishlistItem.objects.get_or_create(
                    wishlist=wishlist, product=product
                )
                if item_created:
                    message = (
                        "Item added to wishlist successfully!"
                        if lang == "en"
                        else "تمت إضافة العنصر إلى قائمة الرغبات بنجاح!"
                    )
                    status = "added"
                else:
                    message = (
                        "Item is already in your wishlist."
                        if lang == "en"
                        else "العنصر موجود بالفعل في قائمة رغباتك."
                    )
                    status = "exists"
                wishlist_count = wishlist.items.count()
        else:
            wishlist_session = request.session.get("wishlist", [])
            if str(product_id) in wishlist_session:
                message = (
                    "Item is already in your wishlist."
                    if lang == "en"
                    else "العنصر موجود بالفعل في قائمة رغباتك."
                )
                status = "exists"
            else:
                wishlist_session.append(str(product_id))
                request.session["wishlist"] = wishlist_session
                message = (
                    "Item added to wishlist successfully!"
                    if lang == "en"
                    else "تمت إضافة العنصر إلى قائمة الرغبات بنجاح!"
                )
                status = "added"
            wishlist_count = len(wishlist_session)

        request.session["wishlist_count"] = wishlist_count
        return JsonResponse(
            {
                "success": True,
                "message": message,
                "status": status,
                "wishlist_total_items": wishlist_count,
            }
        )
    except Exception:
        message = "An error occurred." if lang == "en" else "حدث خطأ."
        return JsonResponse({"success": False, "message": message}, status=500)


@require_POST
def remove_from_wishlist(request):
    lang = getattr(request, "LANGUAGE_CODE", "en")
    try:
        if request.content_type and request.content_type.startswith("application/json"):
            try:
                data = json.loads(request.body)
            except Exception:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Invalid JSON." if lang == "en" else "نص غير صالح.",
                    },
                    status=400,
                )
        else:
            data = request.POST
        product_id = data.get("product_id")
        if not product_id:
            return JsonResponse(
                {
                    "success": False,
                    "message": (
                        "Product ID not provided."
                        if lang == "en"
                        else "معرف المنتج غير موجود."
                    ),
                },
                status=400,
            )
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return JsonResponse(
                {
                    "success": False,
                    "message": (
                        "Product not found." if lang == "en" else "المنتج غير موجود."
                    ),
                },
                status=404,
            )

        if request.user.is_authenticated:
            try:
                wishlist = Wishlist.objects.get(user=request.user)
            except Wishlist.DoesNotExist:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Wishlist not found for user.",
                        "status": "wishlist_missing",
                    },
                    status=404,
                )
            with transaction.atomic():
                deleted_count, _ = WishlistItem.objects.filter(
                    wishlist=wishlist, product=product
                ).delete()
                if deleted_count > 0:
                    wishlist_count = wishlist.items.count()
                    request.session["wishlist_count"] = wishlist_count
                    message = (
                        "Item removed successfully!"
                        if lang == "en"
                        else "تمت إزالة العنصر بنجاح!"
                    )
                    return JsonResponse(
                        {
                            "success": True,
                            "message": message,
                            "wishlist_total_items": wishlist_count,
                            "status": "removed",
                        }
                    )
                else:
                    message = (
                        "Item not found in wishlist."
                        if lang == "en"
                        else "العنصر غير موجود في قائمة الرغبات."
                    )
                    return JsonResponse(
                        {"success": False, "message": message, "status": "not_found"},
                        status=404,
                    )
        else:
            wishlist_session = request.session.get("wishlist", [])
            if str(product_id) in wishlist_session:
                wishlist_session.remove(str(product_id))
                request.session["wishlist"] = wishlist_session
                wishlist_count = len(wishlist_session)
                request.session["wishlist_count"] = wishlist_count
                message = (
                    "Item removed successfully!"
                    if lang == "en"
                    else "تمت إزالة العنصر بنجاح!"
                )
                return JsonResponse(
                    {
                        "success": True,
                        "message": message,
                        "wishlist_total_items": wishlist_count,
                        "status": "removed",
                    }
                )
            else:
                message = (
                    "Item not found in wishlist."
                    if lang == "en"
                    else "العنصر غير موجود في قائمة الرغبات."
                )
                return JsonResponse(
                    {"success": False, "message": message, "status": "not_found"},
                    status=404,
                )
    except Exception:
        message = "An error occurred." if lang == "en" else "حدث خطأ."
        return JsonResponse({"success": False, "message": message}, status=500)


@require_POST
def remove_from_cart(request):
    lang = getattr(request, "LANGUAGE_CODE", "en")
    try:
        if request.content_type and request.content_type.startswith("application/json"):
            try:
                data = json.loads(request.body)
            except Exception:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Invalid JSON." if lang == "en" else "نص غير صالح.",
                    },
                    status=HttpResponseBadRequest.status_code,
                )
        else:
            data = request.POST
        cart_item_id = data.get("cart_item_id")
        if not cart_item_id:
            return JsonResponse(
                {
                    "success": False,
                    "message": (
                        "Cart item ID not provided."
                        if lang == "en"
                        else "معرف عنصر السلة غير موجود."
                    ),
                },
                status=HttpResponseBadRequest.status_code,
            )
        try:
            cart_item_id = int(cart_item_id)
        except ValueError:
            return JsonResponse(
                {
                    "success": False,
                    "message": (
                        "Invalid cart item ID format."
                        if lang == "en"
                        else "تنسيق معرف عنصر السلة غير صالح."
                    ),
                },
                status=HttpResponseBadRequest.status_code,
            )
        try:
            cart_item = get_object_or_404(
                CartItem.objects.select_related("cart"), id=cart_item_id
            )
            if request.user.is_authenticated:
                if cart_item.cart.user != request.user:
                    return JsonResponse(
                        {
                            "success": False,
                            "message": (
                                "Unauthorized action."
                                if lang == "en"
                                else "إجراء غير مصرح به."
                            ),
                        },
                        status=HttpResponseForbidden.status_code,
                    )
            else:
                if cart_item.cart.session_key != request.session.session_key:
                    return JsonResponse(
                        {
                            "success": False,
                            "message": (
                                "Unauthorized action."
                                if lang == "en"
                                else "إجراء غير مصرح به."
                            ),
                        },
                        status=HttpResponseForbidden.status_code,
                    )
            cart = cart_item.cart
            with transaction.atomic():
                cart_item.delete()
                request.session["cart_count"] = cart.total_items
                message = (
                    "Item removed from cart."
                    if lang == "en"
                    else "تمت إزالة العنصر من السلة."
                )
                return JsonResponse(
                    {
                        "success": True,
                        "message": message,
                        "cart_item_id": cart_item_id,
                        "cart_total_items": cart.total_items,
                        "cart_total_price": str(cart.total_price),
                    }
                )
        except CartItem.DoesNotExist:
            message = (
                "Cart item not found."
                if lang == "en"
                else "لم يتم العثور على عنصر في السلة."
            )
            return JsonResponse({"success": False, "message": message}, status=404)
        except Exception as e:
            return JsonResponse(
                {
                    "success": False,
                    "message": f"An unexpected error occurred: {str(e)}",
                },
                status=500,
            )
    except Exception:
        message = "An error occurred." if lang == "en" else "حدث خطأ."
        return JsonResponse({"success": False, "message": message}, status=500)


# --- Cart Views ---
def cart_view(request):
    cart_items_data = []
    total_cart_price = Decimal("0.00")
    shipping_fee = Decimal(config.SHIPPING_RATE_CAIRO)
    cart = None

    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            pass
    else:
        session_key = request.session.session_key
        if session_key:
            try:
                cart = Cart.objects.get(session_key=session_key)
            except Cart.DoesNotExist:
                pass

    if cart:
        cart_items = cart.items.select_related(
            "product_variant__product",
            "product_variant__color",
            "product_variant__size",
        ).order_by("pk")

        for item in cart_items:
            current_stock = (
                item.product_variant.stock_quantity if item.product_variant else 0
            )
            if item.quantity > current_stock:
                item.quantity = current_stock
                item.save()

            if current_stock == 0:
                item.delete()
                continue

            item_total = item.get_total_price()
            total_cart_price += item_total
            cart_items_data.append(
                {
                    "id": item.id,
                    "variant": item.product_variant,
                    "quantity": item.quantity,
                    "total": item_total,
                    "stock_available": current_stock,
                }
            )

        cart.update_totals()
        total_cart_price = cart.total_price_field
        request.session["cart_count"] = cart.total_items_field
    else:
        request.session["cart_count"] = 0

    grand_total = total_cart_price + shipping_fee

    return render(
        request,
        "shop/cart_view.html",
        {
            "items": cart_items_data,
            "total": total_cart_price,
            "shipping_fee": shipping_fee,
            "grand_total": grand_total,
            "cart": cart,
        },
    )


@require_POST
def update_cart_quantity(request):
    try:
        lang = getattr(request, "LANGUAGE_CODE", "en")  # Default to 'en' if not set
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            message = "Invalid JSON." if lang == "en" else "نص غير صالح."
            return JsonResponse(
                {"success": False, "message": message},
                status=HttpResponseBadRequest.status_code,
            )

        cart_item_id = data.get("cart_item_id")
        new_quantity = data.get("quantity")

        if not cart_item_id or new_quantity is None:
            message = (
                "Cart item ID or quantity not provided."
                if lang == "en"
                else "معرف عنصر السلة أو الكمية غير موجود."
            )
            return JsonResponse(
                {"success": False, "message": message},
                status=HttpResponseBadRequest.status_code,
            )

        try:
            cart_item_id = int(cart_item_id)
            new_quantity = int(new_quantity)
        except ValueError:
            message = (
                "Invalid quantity or item ID format."
                if lang == "en"
                else "تنسيق معرف العنصر أو الكمية غير صالح."
            )
            return JsonResponse(
                {"success": False, "message": message},
                status=HttpResponseBadRequest.status_code,
            )

        try:
            cart_item = get_object_or_404(
                CartItem.objects.select_related("cart", "product_variant"),
                id=cart_item_id,
            )
            if request.user.is_authenticated:
                if cart_item.cart.user != request.user:
                    message = (
                        "Unauthorized action." if lang == "en" else "إجراء غير مصرح به."
                    )
                    return JsonResponse(
                        {"success": False, "message": message},
                        status=HttpResponseForbidden.status_code,
                    )
            else:
                if cart_item.cart.session_key != request.session.session_key:
                    message = (
                        "Unauthorized action." if lang == "en" else "إجراء غير مصرح به."
                    )
                    return JsonResponse(
                        {"success": False, "message": message},
                        status=HttpResponseForbidden.status_code,
                    )

            if new_quantity <= 0:
                with transaction.atomic():
                    cart_item.delete()
                message = (
                    "Item removed from cart."
                    if lang == "en"
                    else "تمت إزالة العنصر من السلة."
                )
                status = "removed"
                item_total_price = Decimal("0.00")
            else:
                if cart_item.product_variant.stock_quantity < new_quantity:
                    new_quantity = cart_item.product_variant.stock_quantity
                with transaction.atomic():
                    cart_item.quantity = new_quantity
                    cart_item.save()
                message = (
                    "Cart quantity updated." if lang == "en" else "تم تحديث كمية السلة."
                )
                status = "updated"
                item_total_price = cart_item.get_total_price()

            request.session["cart_count"] = cart_item.cart.total_items
            return JsonResponse(
                {
                    "success": True,
                    "message": message,
                    "status": status,
                    "cart_item_id": cart_item_id,
                    "new_quantity": cart_item.quantity if status == "updated" else 0,
                    "item_total_price": str(item_total_price),
                    "cart_total_items": cart_item.cart.total_items,
                    "cart_total_price": str(cart_item.cart.total_price),
                }
            )

        except CartItem.DoesNotExist:
            message = (
                "Cart item not found."
                if lang == "en"
                else "لم يتم العثور على عنصر في السلة."
            )
            return JsonResponse({"success": False, "message": message}, status=404)

        except Exception as e:
            print(f"Error updating cart quantity: {e}")
            message = (
                f"An unexpected error occurred: {str(e)}"
                if lang == "en"
                else f"حدث خطأ غير متوقع: {str(e)}"
            )
            return JsonResponse({"success": False, "message": message}, status=500)

    except Exception as e:
        message = "An error occurred." if lang == "en" else "حدث خطأ."
        return JsonResponse({"success": False, "message": message}, status=500)


# --- Checkout & Order Views ---
def get_cart_for_request(request):
    if request.user.is_authenticated:
        try:
            return Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return None
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.save()
            session_key = request.session.session_key
        try:
            return Cart.objects.get(session_key=session_key)
        except Cart.DoesNotExist:
            return None


def checkout_view(request):
    cart = get_cart_for_request(request)

    if not cart or not cart.items.exists():
        messages.warning(
            request, _("Your cart is empty. Please add items before checking out.")
        )
        return redirect("shop:cart_view")

    cart.update_totals()
    if cart.total_items == 0:
        messages.warning(
            request,
            _(
                "Your cart is empty after stock adjustments. Please add items before checking out."
            ),
        )
        return redirect("shop:cart_view")

    initial_shipping_data = {}
    user_shipping_addresses = ShippingAddress.objects.none()

    # Fetch user's saved addresses more efficiently
    if request.user.is_authenticated:
        user_shipping_addresses = ShippingAddress.objects.filter(
            user=request.user
        ).distinct()
        if user_shipping_addresses:
            default_address = (
                user_shipping_addresses.filter(is_default=True).first()
                or user_shipping_addresses.order_by("-id").first()
            )
            if default_address:
                initial_shipping_data = {
                    "full_name": default_address.full_name,
                    "address_line1": default_address.address_line1,
                    "address_line2": default_address.address_line2,
                    "city": default_address.city,
                    "phone_number": default_address.phone_number,
                }

    shipping_form = ShippingAddressForm(
        request.POST or None, initial=initial_shipping_data
    )
    payment_form = PaymentForm(request.POST or None)

    # Determine shipping fee based on form input or default address
    city = (
        request.POST.get("city")
        if request.method == "POST"
        else initial_shipping_data.get("city")
    )
    if city == "OUTSIDE_CAIRO":
        # This is now an estimate; the real calculation happens below
        shipping_fee_estimate = Decimal(config.SHIPPING_RATE_OUTSIDE_CAIRO)
    else:
        shipping_fee_estimate = Decimal(config.SHIPPING_RATE_CAIRO)

    # --- New Per-Vendor Shipping Calculation ---
    total_shipping_cost = Decimal("0.00")
    vendor_items = {}
    for item in cart.items.all():
        vendor_id = item.product_variant.product.vendor_id
        if vendor_id not in vendor_items:
            vendor_items[vendor_id] = []
        vendor_items[vendor_id].append(item)

    for vendor_id, items in vendor_items.items():
        vendor_shipping = VendorShipping.objects.filter(vendor_id=vendor_id).first()
        if vendor_shipping:
            subtotal = sum(item.get_total_price() for item in items)
            if not (
                vendor_shipping.free_shipping_threshold
                and subtotal >= vendor_shipping.free_shipping_threshold
            ):
                if city == "OUTSIDE_CAIRO":
                    total_shipping_cost += vendor_shipping.shipping_rate_outside_cairo
                else:
                    total_shipping_cost += vendor_shipping.shipping_rate_cairo

    # --- Coupon Logic for Checkout ---
    coupon_id = request.session.get("coupon_id")
    discount_amount = Decimal("0.00")
    coupon = None
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            if coupon.is_valid():
                if (
                    coupon.min_purchase_amount
                    and cart.total_price_field < coupon.min_purchase_amount
                ):
                    messages.warning(
                        request, _("Coupon is no longer valid for this cart total.")
                    )
                    del request.session["coupon_id"]
                else:
                    if coupon.discount_type == "percentage":
                        discount_amount = (
                            cart.total_price_field * coupon.discount_value
                        ) / 100
                    else:
                        discount_amount = coupon.discount_value
            else:
                del request.session["coupon_id"]
        except Coupon.DoesNotExist:
            del request.session["coupon_id"]

    if request.method == "POST":
        selected_address_id = request.POST.get("saved_address")
        use_new_address = selected_address_id == "new" or not user_shipping_addresses

        if use_new_address:
            # Process with new address form
            if shipping_form.is_valid() and payment_form.is_valid():
                return process_order(
                    request,
                    cart,
                    shipping_form=shipping_form,
                    payment_form=payment_form,
                )
            else:
                messages.error(
                    request,
                    _(
                        "Please correct the errors in your shipping and/or payment details."
                    ),
                )
        else:
            # Existing address selected
            try:
                # Security: Ensure the selected address belongs to the current user
                selected_address = get_object_or_404(
                    ShippingAddress, id=selected_address_id, user=request.user
                )
                if payment_form.is_valid():
                    return process_order(
                        request,
                        cart,
                        payment_form=payment_form,
                        existing_address=selected_address,
                    )
            except (ShippingAddress.DoesNotExist, ValueError):
                messages.error(
                    request, _("Invalid address selected. Please try again.")
                )
                return redirect("shop:checkout")
            else:
                messages.error(
                    request, _("Please correct the errors in your payment details.")
                )

    context = {
        "cart": cart,
        "shipping_form": shipping_form,
        "payment_form": payment_form,
        "user_shipping_addresses": user_shipping_addresses,
        "cart_items": cart.items.all(),
        "subtotal": cart.total_price_field,
        "shipping_fee": total_shipping_cost,
        "discount_amount": discount_amount,
        "grand_total": cart.total_price_field + total_shipping_cost - discount_amount,
    }
    return render(request, "shop/checkout.html", context)


@transaction.atomic
def process_order(
    request, cart, shipping_form=None, payment_form=None, existing_address=None
):
    try:
        if not shipping_form and not existing_address:
            messages.error(request, _("Shipping information is required."))
            return redirect("shop:checkout")

        if not payment_form:
            messages.error(request, _("Payment information is required."))
            return redirect("shop:checkout")

        # --- Final Coupon Validation ---
        coupon_id = request.session.get("coupon_id")
        coupon = None
        discount_amount = Decimal("0.00")
        if coupon_id:
            try:
                coupon = Coupon.objects.get(id=coupon_id)
                if coupon.is_valid() and (
                    not coupon.min_purchase_amount
                    or cart.total_price_field >= coupon.min_purchase_amount
                ):
                    if coupon.discount_type == "percentage":
                        discount_amount = (
                            cart.total_price_field * coupon.discount_value
                        ) / 100
                    else:
                        discount_amount = coupon.discount_value
                else:
                    # Coupon became invalid, proceed without it
                    coupon = None
                    messages.warning(
                        request,
                        _("The applied coupon was invalid and has been removed."),
                    )
            except Coupon.DoesNotExist:
                coupon = None

        # Determine shipping cost from the final address data
        city = (
            shipping_form.cleaned_data.get("city")
            if shipping_form
            else existing_address.city
        )

        # --- New Per-Vendor Shipping Calculation for Order ---
        total_shipping_cost = Decimal("0.00")
        vendor_items = {}
        # Group items by vendor
        for item in cart.items.all():
            vendor_id = item.product_variant.product.vendor_id
            if vendor_id not in vendor_items:
                vendor_items[vendor_id] = []
            vendor_items[vendor_id].append(item)

        for vendor_id, items in vendor_items.items():
            try:
                vendor_shipping = VendorShipping.objects.get(vendor_id=vendor_id)
                subtotal = sum(item.get_total_price() for item in items)
                if not (
                    vendor_shipping.free_shipping_threshold
                    and subtotal >= vendor_shipping.free_shipping_threshold
                ):
                    total_shipping_cost += (
                        vendor_shipping.shipping_rate_outside_cairo
                        if city == "OUTSIDE_CAIRO"
                        else vendor_shipping.shipping_rate_cairo
                    )
            except VendorShipping.DoesNotExist:
                # Fallback to global config if vendor settings are missing
                total_shipping_cost += (
                    Decimal(config.SHIPPING_RATE_OUTSIDE_CAIRO)
                    if city == "OUTSIDE_CAIRO"
                    else Decimal(config.SHIPPING_RATE_CAIRO)
                )

        # Create order
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            full_name=(
                shipping_form.cleaned_data["full_name"]
                if shipping_form
                else existing_address.full_name
            ),
            email=(
                shipping_form.cleaned_data.get("email")
                if shipping_form
                else existing_address.email
            ),
            phone_number=(
                shipping_form.cleaned_data["phone_number"]
                if shipping_form
                else existing_address.phone_number
            ),
            subtotal=Decimal("0.00"),
            shipping_cost=total_shipping_cost,
            grand_total=Decimal("0.00"),
            coupon=coupon,
            discount_amount=discount_amount,
            status="pending",
            payment_status="pending",
        )

        # Save shipping address
        if existing_address:
            # Use a copy of the existing address for this order's record
            shipping_address = existing_address.clone_for_order(order)
        else:
            shipping_address = shipping_form.save(commit=False)
            if request.user.is_authenticated:
                shipping_address.user = request.user
            shipping_address.order = order
            shipping_address.save()

        order.shipping_address = shipping_address
        order.save()

        # Create payment
        payment_data = payment_form.cleaned_data
        payment = Payment.objects.create(
            order=order,
            payment_method=payment_data.get("payment_method"),
            amount=Decimal("0.00"),  # Will update later
            transaction_id=f"TXN-{uuid.uuid4().hex[:10]}",
            is_success=False,
        )

        # Process cart items
        subtotal = Decimal("0.00")
        # Lock product variants to prevent race conditions on stock
        cart_items = cart.items.select_related("product_variant__product").all()
        variants_to_lock = [item.product_variant for item in cart_items]
        locked_variants = list(
            ProductVariant.objects.select_for_update().filter(
                id__in=[v.id for v in variants_to_lock]
            )
        )
        for cart_item in cart_items:
            if variant.stock_quantity < cart_item.quantity:
                raise ValueError(
                    f"Not enough stock for {variant.product.name} "
                    f"({variant.color.name if variant.color else 'N/A'}, "
                    f"{variant.size.name if variant.size else 'N/A'}). "
                    f"Available: {variant.stock_quantity}, Requested: {cart_item.quantity}"
                )

            price = variant.get_price  # property
            OrderItem.objects.create(
                order=order,
                product_variant=variant,
                quantity=cart_item.quantity,
                price_at_purchase=price,
            )
            variant.stock_quantity -= cart_item.quantity
            variant.save()
            subtotal += price * cart_item.quantity

        # --- Create VendorOrder records and calculate commissions ---
        for vendor_id, items in vendor_items.items():
            vendor_profile = VendorProfile.objects.get(id=vendor_id)
            vendor_subtotal = sum(item.get_total_price() for item in items)

            # Calculate this vendor's portion of the shipping
            vendor_shipping_cost = Decimal("0.00")
            try:
                vendor_shipping_settings = VendorShipping.objects.get(
                    vendor=vendor_profile
                )
                if not (
                    vendor_shipping_settings.free_shipping_threshold
                    and vendor_subtotal
                    >= vendor_shipping_settings.free_shipping_threshold
                ):
                    vendor_shipping_cost = (
                        vendor_shipping_settings.shipping_rate_outside_cairo
                        if city == "OUTSIDE_CAIRO"
                        else vendor_shipping_settings.shipping_rate_cairo
                    )
            except VendorShipping.DoesNotExist:
                vendor_shipping_cost = (
                    Decimal(config.SHIPPING_RATE_OUTSIDE_CAIRO)
                    if city == "OUTSIDE_CAIRO"
                    else Decimal(config.SHIPPING_RATE_CAIRO)
                )

            # Calculate commission
            commission_rate = vendor_profile.commission_rate
            commission_amount = (vendor_subtotal * commission_rate) / 100

            # Create the VendorOrder record
            vendor_order = VendorOrder.objects.create(
                order=order,
                vendor=vendor_profile,
                subtotal=vendor_subtotal,
                shipping_charged=vendor_shipping_cost,
                commission_rate=commission_rate,
                commission_amount=commission_amount,
                # net_payout is calculated on save
            )

            # Update vendor's wallet balance
            vendor_profile.wallet_balance += vendor_order.net_payout
            vendor_profile.save(update_fields=["wallet_balance"])

        # Update totals
        order.subtotal = subtotal
        order.grand_total = subtotal + order.shipping_cost - discount_amount
        order.save()

        # Update payment
        payment.amount = order.grand_total
        payment.is_success = True
        payment.save()

        # Finalize order
        order.status = "processing"
        order.payment_status = "paid"
        order.save()

        # Increment coupon usage count
        if coupon:
            coupon.times_used = F("times_used") + 1
            coupon.save()
            del request.session["coupon_id"]

        # Clear cart
        cart.items.all().delete()
        cart.update_totals()
        if not request.user.is_authenticated:
            cart.delete()
        request.session["cart_count"] = 0

        messages.success(
            request, _(f"Your order {order.order_number} has been placed successfully!")
        )
        return redirect("shop:order_confirmation", order_number=order.order_number)

    except ValueError as e:
        messages.error(request, _(f"Order failed: {e}"))
        return redirect("shop:checkout")
    except Exception as e:
        logger.exception(f"Order processing failed for user {request.user}: {e}")
        messages.error(request, _(f"An unexpected error occurred during checkout: {e}"))
        return redirect("shop:checkout")


def order_confirmation(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)

    if order.user != request.user and order.user is not None:
        return render(request, "shop/order_not_found.html", status=403)

    order_items = order.items.select_related(
        "product_variant__product", "product_variant__color", "product_variant__size"
    )

    return render(
        request,
        "shop/order_confirmation.html",
        {"order": order, "order_items": order_items},
    )


def order_detail(request, order_number):
    if request.user.is_authenticated:
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
    else:
        order = get_object_or_404(Order, order_number=order_number, user=None)
    order_items = order.items.select_related(
        "product_variant__product", "product_variant__color", "product_variant__size"
    ).all()
    return render(
        request, "shop/order_detail.html", {"order": order, "order_items": order_items}
    )


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    paginator = Paginator(orders, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "shop/order_history.html", {"orders": page_obj})


def get_available_sizes_ajax(request, product_id):
    """
    AJAX endpoint to get available sizes based on product and selected color.
    """
    if (
        request.method == "GET"
        and request.headers.get("x-requested-with") == "XMLHttpRequest"
    ):
        color_id = request.GET.get("color_id")
        try:
            # You should have a Product model with a method like get_available_sizes
            product = get_object_or_404(Product, id=product_id)
            available_sizes_query = product.get_available_sizes(color_id=color_id)

            # Convert queryset to a list of dictionaries for JSON response
            # Change 'available_sizes' to 'sizes' to match JavaScript
            available_sizes_data = list(available_sizes_query.values("id", "name"))

            return JsonResponse({"success": True, "sizes": available_sizes_data})
        except Product.DoesNotExist:
            return JsonResponse(
                {"success": False, "message": "Product not found."}, status=404
            )
    return JsonResponse({"success": False, "message": "Invalid request"}, status=400)


def vendor_detail(request, slug):
    # 1. Get the VendorProfile instance
    vendor_profile = get_object_or_404(VendorProfile, slug=slug)

    # 2. Access the related MnoryUser instance from the VendorProfile
    # As per your models.py, VendorProfile has a OneToOneField named 'user'
    # which points to settings.AUTH_USER_MODEL (your MnoryUser).
    vendor_user_instance = vendor_profile.user

    # Get products for this vendor, filtered by the VendorProfile instance
    products_queryset = Product.objects.filter(vendor=vendor_profile, is_active=True)

    # Apply filters
    price_min = request.GET.get("price_min")
    price_max = request.GET.get("price_max")
    category_id = request.GET.get("category")
    brand_id = request.GET.get("brand")
    colors_ids = request.GET.getlist(
        "colors"
    )  # request.GET.getlist returns a list of selected IDs
    sizes_ids = request.GET.getlist(
        "sizes"
    )  # request.GET.getlist returns a list of selected IDs
    sort_by = request.GET.get("sort", "-created_at")  # Default sort to newest first

    # Apply price filters
    if price_min:
        products_queryset = products_queryset.filter(price__gte=price_min)
    if price_max:
        products_queryset = products_queryset.filter(price__lte=price_max)

    # Apply category filter (accept either numeric id or slug)
    if category_id:
        if str(category_id).isdigit():
            products_queryset = products_queryset.filter(category_id=int(category_id))
        else:
            products_queryset = products_queryset.filter(category__slug=category_id)

    # Apply brand filter (accept either numeric id or slug)
    if brand_id:
        if str(brand_id).isdigit():
            products_queryset = products_queryset.filter(brand_id=int(brand_id))
        else:
            # support brand slug values (e.g., 'puma') or brand name
            products_queryset = products_queryset.filter(
                Q(brand__slug=brand_id) | Q(brand__name=brand_id)
            )

    # Apply colors filter (ManyToManyField through ProductColor)
    if colors_ids:
        # Filter products that have at least one of the selected colors through the ProductColor intermediate model
        products_queryset = products_queryset.filter(
            productcolor__color__id__in=colors_ids
        ).distinct()

    # Apply sizes filter (ManyToManyField through ProductSize)
    if sizes_ids:
        # Filter products that have at least one of the selected sizes through the ProductSize intermediate model
        products_queryset = products_queryset.filter(
            productsize__size__id__in=sizes_ids
        ).distinct()

    # Apply sorting
    products_queryset = products_queryset.order_by(sort_by)

    # Pagination
    paginator = Paginator(products_queryset, 9)  # Show 9 products per page
    page = request.GET.get("page")
    try:
        products_page = paginator.page(page)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)

    # Get filter options relevant to this vendor's active products
    # CORRECTED based on your models.py:
    # - Category and Brand use related_name='products' on Product model
    # - Color and Size use through models ProductColor and ProductSize respectively.

    # Filter Categories that have active products from this vendor
    categories = Category.objects.filter(
        products__vendor=vendor_profile, products__is_active=True
    ).distinct()

    # Filter Brands that have active products from this vendor
    brands = Brand.objects.filter(
        products__vendor=vendor_profile, products__is_active=True
    ).distinct()

    # Filter Colors that are associated with active products from this vendor via ProductColor
    colors = Color.objects.filter(
        productcolor__product__vendor=vendor_profile,
        productcolor__product__is_active=True,
    ).distinct()

    # Filter Sizes that are associated with active products from this vendor via ProductSize
    sizes = Size.objects.filter(
        productsize__product__vendor=vendor_profile,
        productsize__product__is_active=True,
    ).distinct()

    # Get min/max price for the vendor's products (for filter range)
    price_range = Product.objects.filter(
        vendor=vendor_profile, is_active=True
    ).aggregate(Min("price"), Max("price"))
    # Ensure price_range has a default if no products exist
    min_price_val = (
        price_range["price__min"] if price_range["price__min"] is not None else 0
    )
    max_price_val = (
        price_range["price__max"] if price_range["price__max"] is not None else 0
    )

    # Vendor stats
    vendor_stats = {
        "total_products": Product.objects.filter(
            vendor=vendor_profile, is_active=True
        ).count(),
        # Count categories that have active products from this vendor
        "categories_count": categories.count(),  # We already filtered `categories` above
    }

    # Related vendors: other vendors producing in the same categories
    related_qs = (
        VendorProfile.objects.filter(
            products__category__in=categories, products__is_active=True
        )
        .exclude(id=vendor_profile.id)
        .distinct()[:6]
    )

    # Ensure we have a safe vendor_location string for templates (some VendorProfile instances may not have `location`)
    vendor_location = getattr(vendor_profile, "location", "") or ""

    # Build a safe list of small dicts for related vendors to avoid missing attribute errors in templates
    related_vendors = []
    for rv in related_qs:
        # logo url if present
        logo_url = None
        try:
            if getattr(rv, "logo", None):
                logo_url = rv.logo.url
        except Exception:
            logo_url = None

        # safe location (use get_location_display if available)
        if hasattr(rv, "get_location_display"):
            try:
                safe_location = rv.get_location_display() or ""
            except Exception:
                safe_location = getattr(rv, "location", "") or ""
        else:
            safe_location = getattr(rv, "location", "") or ""

        related_vendors.append(
            {
                "slug": getattr(rv, "slug", ""),
                "store_name": getattr(rv, "store_name", ""),
                "logo_url": logo_url,
                "safe_location": safe_location,
            }
        )

    # Vendor reviews (if freelancing.Review exists) where the reviewee is the vendor's user
    vendor_reviews = []
    try:
        if vendor_user_instance:
            vendor_reviews = Review.objects.filter(
                reviewee=vendor_user_instance, is_public=True
            ).order_by("-created_at")[:5]
    except Exception:
        vendor_reviews = []

    context = {
        "vendor": vendor_profile,  # Pass the VendorProfile instance to the template
        "products": products_page,
        "categories": categories,
        "brands": brands,
        "colors": colors,
        "sizes": sizes,
        "price_range": {
            "price__min": min_price_val,
            "price__max": max_price_val,
        },  # Pass adjusted price_range
        "vendor_stats": vendor_stats,
        "related_vendors": related_vendors,
        "vendor_location": vendor_location,
        "vendor_reviews": vendor_reviews,
    }
    return render(request, "shop/vendor_detail.html", context)


# --- Advertisement Tracking Views ---
@require_POST
def track_ad_view(request):
    """Track advertisement view count via AJAX."""
    try:
        import json
        from .models import Advertisement

        data = json.loads(request.body)
        ad_id = data.get("ad_id")

        if not ad_id:
            return JsonResponse({"error": "Ad ID required"}, status=400)

        ad = Advertisement.objects.filter(id=ad_id, is_active=True).first()
        if not ad:
            return JsonResponse({"error": "Advertisement not found"}, status=404)

        # Increment view count
        ad.increment_view_count()

        # Refresh from database to get actual count
        ad.refresh_from_db()

        return JsonResponse({"success": True, "view_count": ad.view_count})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def profile_view(request):
    recent_orders = Order.objects.filter(user=request.user).order_by("-created_at")[:5]
    context = {"recent_orders": recent_orders}
    return render(request, "accounts/profile.html", context)


@login_required
def edit_profile(request):
    if request.method == "POST":
        form = UserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Profile updated successfully!"))
            return redirect("shop:profile")
    else:
        form = UserChangeForm(instance=request.user)
    return render(request, "accounts/edit_profile.html", {"form": form})


@login_required
def address_list(request):
    addresses = ShippingAddress.objects.filter(user=request.user)
    return render(request, "accounts/address_list.html", {"addresses": addresses})


@login_required
def address_add(request):
    if request.method == "POST":
        form = ShippingAddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, _("Address added successfully!"))
            return redirect("shop:address_list")
    else:
        form = ShippingAddressForm()
    return render(request, "accounts/address_form.html", {"form": form})


@login_required
def address_edit(request, address_id):
    address = get_object_or_404(ShippingAddress, id=address_id, user=request.user)
    if request.method == "POST":
        form = ShippingAddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, _("Address updated successfully!"))
            return redirect("shop:address_list")
    else:
        form = ShippingAddressForm(instance=address)
    return render(request, "accounts/address_form.html", {"form": form})


@login_required
@require_POST
def address_delete(request, address_id):
    address = get_object_or_404(ShippingAddress, id=address_id, user=request.user)
    address.delete()
    messages.success(request, _("Address deleted successfully!"))
    return redirect("shop:address_list")


@login_required
def account_settings(request):
    from django.contrib.auth.forms import PasswordChangeForm
    from django.contrib.auth import update_session_auth_hash

    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, _("Your password was successfully updated!"))
            return redirect("shop:account_settings")
        else:
            messages.error(request, _("Please correct the error below."))
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "accounts/account_settings.html", {"form": form})


@login_required
def vendor_dashboard(request):
    if not request.user.is_vendor_type:
        # from django.contrib import messages
        messages.error(request, _("Access denied. This page is for vendors only."))
        return redirect("shop:home")

    vendor_profile = get_object_or_404(VendorProfile, user=request.user)

    # Stats
    total_products = Product.objects.filter(vendor=vendor_profile).count()
    vendor_order_items = OrderItem.objects.filter(
        product_variant__product__vendor=vendor_profile
    )
    total_sales = (
        vendor_order_items.aggregate(total=Sum("price_at_purchase"))["total"] or 0
    )
    recent_orders = (
        Order.objects.filter(items__in=vendor_order_items)
        .distinct()
        .order_by("-created_at")[:5]
    )

    # Top Selling Products
    top_products = (
        Product.objects.filter(vendor=vendor_profile, is_active=True)
        .annotate(
            total_sold=Sum("variants__orderitem__quantity"),
            total_revenue=Sum(
                F("variants__orderitem__quantity")
                * F("variants__orderitem__price_at_purchase")
            ),
        )
        .filter(total_sold__gt=0)
        .order_by("-total_sold")[:5]
    )
    # Chart Data: Sales for the last 7 days
    # Get recent product reviews
    recent_reviews = (
        Review.objects.filter(product__vendor=vendor_profile)
        .select_related("reviewer", "product")
        .order_by("-created_at")[:5]
    )

    today = timezone.now().date()
    seven_days_ago = today - timedelta(days=6)

    sales_data = (
        vendor_order_items.filter(order__created_at__date__gte=seven_days_ago)
        .annotate(day=TruncDay("order__created_at"))
        .values("day")
        .annotate(daily_sales=Sum("price_at_purchase"))
        .order_by("day")
    )

    # Prepare data for Chart.js
    chart_labels = [
        (seven_days_ago + timedelta(days=i)).strftime("%b %d") for i in range(7)
    ]
    chart_sales_data = [0.0] * 7
    sales_dict = {
        item["day"].strftime("%b %d"): float(item["daily_sales"]) for item in sales_data
    }
    for i, label in enumerate(chart_labels):
        if label in sales_dict:
            chart_sales_data[i] = sales_dict[label]

    context = {
        "vendor_profile": vendor_profile,
        "total_products": total_products,
        "total_sales": total_sales,
        "recent_orders": recent_orders,
        "recent_reviews": recent_reviews,
        "top_products": top_products,
        "chart_labels": json.dumps(chart_labels),
        "chart_sales_data": json.dumps(chart_sales_data),
    }
    return render(request, "shop/vendor_dashboard.html", context)


@login_required
def vendor_manage_products(request):
    if not request.user.is_vendor_type:
        messages.error(request, _("Access denied. This page is for vendors only."))
        return redirect("shop:home")

    vendor_profile = get_object_or_404(VendorProfile, user=request.user)
    products_list = Product.objects.filter(vendor=vendor_profile).order_by(
        "-created_at"
    )

    # Search and Filter
    search_query = request.GET.get("q", "")
    status_filter = request.GET.get("status", "")

    if search_query:
        products_list = products_list.filter(
            Q(name__icontains=search_query) | Q(sku__icontains=search_query)
        )

    if status_filter:
        products_list = products_list.filter(is_active=(status_filter == "active"))

    paginator = Paginator(products_list, 10)  # 10 products per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "products": page_obj,
        "vendor_profile": vendor_profile,
        "search_query": search_query,
        "status_filter": status_filter,
    }
    return render(request, "shop/vendor_manage_products.html", context)


@login_required
def vendor_add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.vendor = request.user.vendorprofile
            product.save()
            form.save_m2m()  # For many-to-many fields if any
            messages.success(request, _("Product added successfully!"))
            return redirect("shop:vendor_manage_products")
    else:
        form = ProductForm()
    context = {"form": form, "title": _("Add New Product")}
    return render(request, "shop/vendor_product_form.html", context)


@login_required
def vendor_edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    # Ensure the product belongs to the logged-in vendor
    if product.vendor != request.user.vendorprofile:
        messages.error(request, _("You do not have permission to edit this product."))
        return redirect("shop:vendor_manage_products")

    if request.method == "POST":
        product_form = ProductForm(
            request.POST, request.FILES, instance=product, prefix="product"
        )
        image_formset = ProductImageFormSet(
            request.POST, request.FILES, instance=product, prefix="images"
        )
        variant_formset = ProductVariantFormSet(
            request.POST, request.FILES, instance=product, prefix="variants"
        )

        if (
            product_form.is_valid()
            and variant_formset.is_valid()  # noqa
            and image_formset.is_valid()
        ):
            product_form.save()
            variants = variant_formset.save(commit=False)

            # Save images before variants
            images = image_formset.save(commit=False)
            for image in images:
                image.product = product
                image.save()
            for form in image_formset.deleted_forms:
                if form.instance.pk:
                    form.instance.delete()

            for variant in variants:
                variant.product = product
                variant.save()

            for form in variant_formset.deleted_forms:
                if form.instance.pk:
                    form.instance.delete()

            # Recalculate total stock for the main product
            total_stock = (
                product.variants.aggregate(total=Sum("stock_quantity"))["total"] or 0
            )
            product.stock_quantity = total_stock
            product.save(update_fields=["stock_quantity"])

            # Automatically set the first image as main if none is selected
            product.refresh_from_db()
            if (
                product.images.exists()
                and not product.images.filter(is_main=True).exists()
            ):
                first_image = product.images.order_by("order").first()
                if first_image:
                    first_image.is_main = True
                    first_image.save(update_fields=["is_main"])

            messages.success(request, _("Product updated successfully!"))
            return redirect("shop:vendor_manage_products")
    else:
        product_form = ProductForm(instance=product, prefix="product")
        image_formset = ProductImageFormSet(instance=product, prefix="images")
        variant_formset = ProductVariantFormSet(instance=product, prefix="variants")

    context = {
        "form": product_form,
        "image_formset": image_formset,
        "variant_formset": variant_formset,
        "title": _("Edit Product"),
    }
    return render(request, "shop/vendor_product_form.html", context)


@login_required
@require_POST
def vendor_reply_to_review(request, review_id):
    if not request.user.is_vendor_type:
        return JsonResponse(
            {"success": False, "message": _("Access denied.")}, status=403
        )

    review = get_object_or_404(Review, id=review_id)

    # Security check: ensure the product belongs to the current vendor
    if review.product.vendor != request.user.vendorprofile:
        return JsonResponse(
            {
                "success": False,
                "message": _("You do not have permission to reply to this review."),
            },
            status=403,
        )

    form = ReviewReplyForm(request.POST, instance=review)
    if form.is_valid():
        reply = form.save(commit=False)
        reply.replied_at = timezone.now()
        reply.save()
        return JsonResponse(
            {
                "success": True,
                "reply_text": reply.reply,
                "replied_at": timezone.localtime(reply.replied_at).strftime(
                    "%b %d, %Y"
                ),
            }
        )
    else:
        return JsonResponse({"success": False, "errors": form.errors}, status=400)


@login_required
@require_POST
def vendor_delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    # Ensure the product belongs to the logged-in vendor
    if product.vendor != request.user.vendorprofile:
        return JsonResponse(
            {
                "success": False,
                "message": _("You do not have permission to delete this product."),
            },
            status=403,
        )

    try:
        product.delete()
        return JsonResponse(
            {"success": True, "message": _("Product deleted successfully.")}
        )
    except Exception as e:
        logger.error(
            f"Error deleting product {product_id} by user {request.user.email}: {e}"
        )
        return JsonResponse(
            {
                "success": False,
                "message": _("An error occurred while deleting the product."),
            },
            status=500,
        )


@login_required
def vendor_manage_reviews(request):
    if not request.user.is_vendor_type:
        messages.error(request, _("Access denied. This page is for vendors only."))
        return redirect("shop:home")

    vendor_profile = get_object_or_404(VendorProfile, user=request.user)

    review_list = (
        Review.objects.filter(product__vendor=vendor_profile)
        .select_related("user", "product")
        .order_by("-created_at")
    )

    # Search and Filter
    search_query = request.GET.get("q", "")
    rating_filter = request.GET.get("rating", "")

    if search_query:
        review_list = review_list.filter(
            Q(product__name__icontains=search_query)
            | Q(user__email__icontains=search_query)
            | Q(comment__icontains=search_query)
        )

    if rating_filter:
        review_list = review_list.filter(rating=rating_filter)

    paginator = Paginator(review_list, 10)  # 10 reviews per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "reviews": page_obj,
        "search_query": search_query,
        "rating_filter": rating_filter,
    }
    return render(request, "shop/vendor_manage_reviews.html", context)


@login_required
def vendor_manage_shipping(request):
    """
    Page for vendors to manage their shipping costs.
    """
    if not request.user.is_vendor_type:
        messages.error(request, _("Access denied. This page is for vendors only."))
        return redirect("shop:home")

    vendor_profile = get_object_or_404(VendorProfile, user=request.user)
    # get_or_create ensures this works even if the signal failed for an old vendor
    shipping_settings, created = VendorShipping.objects.get_or_create(
        vendor=vendor_profile
    )

    if request.method == "POST":
        form = VendorShippingForm(request.POST, instance=shipping_settings)
        if form.is_valid():
            form.save()
            messages.success(
                request, _("Your shipping settings have been updated successfully.")
            )
            return redirect("shop:vendor_manage_shipping")
    else:
        form = VendorShippingForm(instance=shipping_settings)

    context = {"form": form, "vendor_profile": vendor_profile}
    return render(request, "shop/vendor_manage_shipping.html", context)


@login_required
@require_POST
def vendor_request_payout(request):
    """
    Handles a vendor's request for a payout from their wallet.
    """
    if not request.user.is_vendor_type:
        messages.error(request, _("Access denied."))
        return redirect("shop:home")

    vendor_profile = get_object_or_404(VendorProfile, user=request.user)
    form = PayoutRequestForm(request.POST, vendor_profile=vendor_profile)

    if form.is_valid():
        amount = form.cleaned_data["amount"]
        with transaction.atomic():
            # Lock the vendor profile row to prevent race conditions
            vendor = VendorProfile.objects.select_for_update().get(id=vendor_profile.id)
            if amount <= vendor.wallet_balance:
                vendor.wallet_balance -= amount
                vendor.save(update_fields=["wallet_balance"])
                Payout.objects.create(vendor=vendor, amount=amount, status="pending")
                messages.success(
                    request,
                    _(
                        f"Your payout request for {amount} EGP has been submitted for review."
                    ),
                )
            else:
                messages.error(
                    request, _("Insufficient wallet balance for this payout request.")
                )
    else:
        messages.error(
            request, _("Invalid amount requested. Please check the form and try again.")
        )

    return redirect("shop:vendor_dashboard")


@require_POST
def track_ad_click(request):
    """Track advertisement click count via AJAX."""
    try:
        import json
        from .models import Advertisement

        data = json.loads(request.body)
        ad_id = data.get("ad_id")

        if not ad_id:
            return JsonResponse({"error": "Ad ID required"}, status=400)

        ad = Advertisement.objects.filter(id=ad_id, is_active=True).first()
        if not ad:
            return JsonResponse({"error": "Advertisement not found"}, status=404)

        # Increment click count
        ad.increment_click_count()

        # Refresh from database to get actual count
        ad.refresh_from_db()

        return JsonResponse({"success": True, "click_count": ad.click_count})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
