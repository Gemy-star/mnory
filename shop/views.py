
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.db.models import Q, Min, Max, Sum
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import json
from .forms import RegisterForm, LoginForm, ShippingAddressForm, PaymentForm
from .models import (
    Category, SubCategory, FitType, Brand, Color, Size,
    Product, ProductVariant, Cart, CartItem, Wishlist, WishlistItem, HomeSlider,
    Order, OrderItem, ShippingAddress, Payment, MnoryUser, VendorProfile
)
from decimal import Decimal
import uuid
import logging
from django.utils.translation import gettext as _
from constance import config
# Set up logger
logger = logging.getLogger(__name__)


# --- Helper Functions for Filtering/Sorting ---
def _filter_and_sort_products(products_queryset, request_get_params):
    """
    Applies common filtering and sorting logic to a product queryset.
    """
    subcategory_filter = request_get_params.get('subcategory')
    fit_type_filter = request_get_params.get('fit_type')
    brand_filter = request_get_params.get('brand')
    color_filter = request_get_params.get('color')
    size_filter = request_get_params.get('size')
    min_price_str = request_get_params.get('min_price')
    max_price_str = request_get_params.get('max_price')
    sort_by = request_get_params.get('sort', 'name')

    if subcategory_filter:
        products_queryset = products_queryset.filter(subcategory__slug=subcategory_filter)

    if fit_type_filter:
        products_queryset = products_queryset.filter(fit_type__slug=fit_type_filter)

    if brand_filter:
        products_queryset = products_queryset.filter(brand__slug=brand_filter)

    if color_filter:
        # Filter products by color of their available variants
        products_queryset = products_queryset.filter(productvariant__color__slug=color_filter).distinct()

    if size_filter:
        # Filter products by size of their available variants
        products_queryset = products_queryset.filter(productvariant__size__name__iexact=size_filter).distinct()

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
    if sort_by == 'price_low':
        products_queryset = products_queryset.order_by('price')
    elif sort_by == 'price_high':
        products_queryset = products_queryset.order_by('-price')
    elif sort_by == 'newest':
        products_queryset = products_queryset.order_by('-created_at')
    elif sort_by == 'popular':
        # Consider adding a sales count or view count to Product model for true popularity
        products_queryset = products_queryset.order_by('-is_best_seller', '-created_at')
    else:  # Default or invalid sort
        products_queryset = products_queryset.order_by('name')

    return products_queryset.distinct()  # Use distinct to avoid duplicates from many-to-many filters


# --- Core Product & Category Views ---
def home(request):
    """Homepage view"""
    # Optimized initial product queries to reduce database hits
    # Use prefetch_related for images and select_related for foreign keys
    base_products = Product.objects.filter(is_active=True, is_available=True).prefetch_related('images') \
        .select_related('category', 'subcategory', 'brand')

    featured_products = base_products.filter(is_featured=True).distinct()[:8]
    new_arrivals = base_products.filter(is_new_arrival=True).distinct()[:8]
    best_sellers = base_products.filter(is_best_seller=True).distinct()[:8]
    all_products_recent = base_products.order_by('-created_at').distinct()[:8]  # Most recent based on creation
    sale_products = base_products.filter(is_on_sale=True).distinct()[:8]

    categories = Category.objects.filter(is_active=True).order_by('name')
    sliders = HomeSlider.objects.filter(is_active=True).order_by('order')

    products_in_wishlist_ids = []
    if request.user.is_authenticated:
        try:
            # Efficiently get wishlist product IDs for the logged-in user
            wishlist = Wishlist.objects.only('id').get(user=request.user)
            products_in_wishlist_ids = list(wishlist.items.values_list('product_id', flat=True))
        except Wishlist.DoesNotExist:
            pass  # No wishlist yet for this user

    context = {
        'featured_products': featured_products,
        'new_arrivals': new_arrivals,
        'best_sellers': best_sellers,
        'sale_products': sale_products,
        'categories': categories,
        'sliders': sliders,
        'all_products': all_products_recent,  # Renamed for clarity
        'products_in_wishlist_ids': products_in_wishlist_ids,
    }

    return render(request, 'shop/home.html', context)

def category_detail(request, slug):
    """Category detail view - supports 'all' to show all products"""
    category = None
    subcategories = []
    # Start with active and available products
    products_queryset = Product.objects.filter(is_active=True, is_available=True) \
        .prefetch_related('images') \
        .select_related('category', 'subcategory', 'brand')

    if slug and slug != 'all':
        category = get_object_or_404(Category, slug=slug, is_active=True)
        subcategories = category.subcategories.filter(is_active=True).order_by('name')
        products_queryset = products_queryset.filter(category=category)
    elif not slug or slug == 'all':
        # If slug is 'all', products_queryset remains unfiltered by category
        pass
    else:
        messages.error(request, _("Invalid category selected."))
        return redirect('shop:home')  # Redirect to home or all products view

    # Apply filters and sorting using helper. Pass request object to helper for messages
    products_queryset = _filter_and_sort_products(products_queryset, request.GET)

    # Price range calculation for the *entire* filtered set, before pagination
    price_range = products_queryset.aggregate(Min('price'), Max('price'))

    # Pagination
    paginator = Paginator(products_queryset, 12)  # 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Filter options: Only show options relevant to products in the current category/filter set
    # Use correct related names for reverse relations
    fit_types = FitType.objects.filter(is_active=True, products__in=products_queryset).distinct().order_by('name')
    brands = Brand.objects.filter(is_active=True, products__in=products_queryset).distinct().order_by('name')
    colors = Color.objects.filter(is_active=True, productvariant__product__in=products_queryset).distinct().order_by('name')
    sizes = Size.objects.filter(is_active=True, productvariant__product__in=products_queryset).distinct().order_by('name')

    all_categories = Category.objects.filter(is_active=True).order_by('name')  # For navbar/sidebar

    products_in_wishlist_ids = []
    if request.user.is_authenticated:
        try:
            wishlist = Wishlist.objects.only('id').get(user=request.user)
            products_in_wishlist_ids = list(wishlist.items.values_list('product_id', flat=True))
        except Wishlist.DoesNotExist:
            pass

    context = {
        'category': category,
        'subcategories': subcategories,
        'products': page_obj,  # This is the paginated queryset
        'fit_types': fit_types,
        'brands': brands,
        'colors': colors,
        'sizes': sizes,
        'price_range': price_range,
        'categories': all_categories,
        'products_in_wishlist_ids': products_in_wishlist_ids,
        'current_filters': {
            'subcategory': request.GET.get('subcategory'),
            'fit_type': request.GET.get('fit_type'),
            'brand': request.GET.get('brand'),
            'color': request.GET.get('color'),
            'size': request.GET.get('size'),
            'min_price': request.GET.get('min_price'),
            'max_price': request.GET.get('max_price'),
            'sort': request.GET.get('sort', 'name'),
        }
    }

    return render(request, 'shop/category_detail.html', context)
def subcategory_detail(request, category_slug, slug):
    """Subcategory detail view"""
    category = get_object_or_404(Category, slug=category_slug, is_active=True)
    subcategory = get_object_or_404(SubCategory, slug=slug, category=category, is_active=True)

    products_queryset = Product.objects.filter(
        subcategory=subcategory,
        is_active=True,
        is_available=True
    ).prefetch_related('images') \
     .select_related('category', 'subcategory', 'brand')

    # Apply filters and sorting using helper
    products_queryset = _filter_and_sort_products(products_queryset, request.GET)

    # Price range calculation for current filtered set
    price_range = products_queryset.aggregate(Min('price'), Max('price'))

    # Pagination
    paginator = Paginator(products_queryset, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get filter options relevant to this subcategory's products
    fit_types = FitType.objects.filter(is_active=True, products__in=products_queryset).distinct().order_by('name')
    brands = Brand.objects.filter(is_active=True, products__in=products_queryset).distinct().order_by('name')
    colors = Color.objects.filter(is_active=True, productvariant__product__in=products_queryset).distinct().order_by('name')
    sizes = Size.objects.filter(is_active=True, productvariant__product__in=products_queryset).distinct().order_by('name')

    all_categories = Category.objects.filter(is_active=True).order_by('name')  # For sidebar navigation

    products_in_wishlist_ids = []
    if request.user.is_authenticated:
        try:
            wishlist = Wishlist.objects.only('id').get(user=request.user)
            products_in_wishlist_ids = list(wishlist.items.values_list('product_id', flat=True))
        except Wishlist.DoesNotExist:
            pass

    context = {
        'category': category,
        'subcategory': subcategory,
        'products': page_obj,
        'fit_types': fit_types,
        'brands': brands,
        'colors': colors,
        'sizes': sizes,
        'price_range': price_range,
        'categories': all_categories,
        'subcategories': category.subcategories.filter(is_active=True).order_by('name'),
        'products_in_wishlist_ids': products_in_wishlist_ids,
        'current_filters': {
            'subcategory': request.GET.get('subcategory'),  # This will be the current subcategory
            'fit_type': request.GET.get('fit_type'),
            'brand': request.GET.get('brand'),
            'color': request.GET.get('color'),
            'size': request.GET.get('size'),
            'min_price': request.GET.get('min_price'),
            'max_price': request.GET.get('max_price'),
            'sort': request.GET.get('sort', 'name'),
        }
    }

    return render(request, 'shop/subcategory_detail.html', context)
def product_detail(request, slug):
    """Product detail view"""
    product = get_object_or_404(
        Product.objects.select_related('category', 'subcategory', 'brand', 'fit_type')
        .prefetch_related('images', 'variants__color', 'variants__size'),
        slug=slug,
        is_active=True,
        is_available=True
    )

    related_products = Product.objects.filter(
        Q(category=product.category) | Q(subcategory=product.subcategory),
        is_active=True,
        is_available=True
    ).exclude(id=product.id).distinct().prefetch_related('images') \
                           .select_related('category', 'subcategory', 'brand')[:8]

    variants = product.variants.filter(is_available=True, stock_quantity__gt=0)

    available_colors = Color.objects.filter(
        productvariant__in=variants,
        is_active=True
    ).distinct().order_by('name') # Keep this if you want colors sorted alphabetically by name

    available_sizes = Size.objects.filter(
        productvariant__in=variants,
        is_active=True
    ).distinct() # REMOVE .order_by('name') to use Size model's Meta.ordering

    product_images = product.images.all().order_by('order')

    categories = Category.objects.filter(is_active=True).order_by('name')

    is_in_wishlist = False
    if request.user.is_authenticated:
        is_in_wishlist = WishlistItem.objects.filter(
            wishlist__user=request.user, product=product
        ).exists()

    context = {
        'product': product,
        'related_products': related_products,
        'variants': variants,
        'available_colors': available_colors,
        'available_sizes': available_sizes, # This will now be ordered by size_type, then 'order', then 'name'
        'product_images': product_images,
        'categories': categories,
        'is_in_wishlist': is_in_wishlist,
    }

    return render(request, 'shop/product_detail.html', context)
# --- Search & API Endpoints ---
@require_http_methods(["GET"])
def search_products(request):
    """AJAX search for products"""
    query = request.GET.get('q', '').strip()  # .strip() to remove leading/trailing whitespace

    if not query or len(query) < 2:
        return JsonResponse({'products': []})

    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query) |
        Q(brand__name__icontains=query) |
        Q(category__name__icontains=query),
        is_active=True,
        is_available=True
    ).select_related('category', 'subcategory', 'brand').prefetch_related('images')[
               :10]  # Limit results for performance

    results = []
    for product in products:
        main_image = product.get_main_image()  # Assuming this method gets the main image object
        results.append({
            'id': product.id,
            'name': product.name,
            'price': str(product.get_price()),  # Ensure price is a string for JSON serialization
            'url': product.get_absolute_url(),
            'image': main_image.image.url if main_image and main_image.image else '',  # Check if image file exists
            'category': product.category.name if product.category else '',
            'brand': product.brand.name if product.brand else '',
        })

    return JsonResponse({'products': results})


@require_http_methods(["GET"])
def get_product_variants(request, product_id):
    """
    AJAX endpoint to get product variants based on color and size filters.
    Returns a list of matching variants with stock info.
    """
    try:
        product = get_object_or_404(Product, id=product_id)
    except ValueError:
        return JsonResponse({'variants': [], 'message': _("Invalid product ID.")}, status=400)

    color_id = request.GET.get('color')
    size_id = request.GET.get('size')

    variants_queryset = ProductVariant.objects.filter(
        product=product,
        is_available=True,
        stock_quantity__gt=0  # Only show variants that are in stock
    ).select_related('color', 'size')  # Efficiently fetch related color and size objects

    if color_id:
        try:
            variants_queryset = variants_queryset.filter(color__id=int(color_id))
        except (ValueError, TypeError):
            # If color_id is invalid, return empty results (or all if that's desired behavior)
            return JsonResponse({'variants': [], 'message': _("Invalid color ID.")}, status=400)

    if size_id:
        try:
            variants_queryset = variants_queryset.filter(size__id=int(size_id))
        except (ValueError, TypeError):
            # If size_id is invalid, return empty results
            return JsonResponse({'variants': [], 'message': _("Invalid size ID.")}, status=400)

    results = []
    for variant in variants_queryset:
        results.append({
            'id': variant.id,
            'color_id': variant.color.id if variant.color else None,
            'color_name': variant.color.name if variant.color else _('N/A'),
            'size_id': variant.size.id if variant.size else None,
            'size_name': variant.size.name if variant.size else _('N/A'),
            'price': str(variant.get_price()),  # Ensure Decimal is serialized as string
            'stock': variant.stock_quantity,
            'sku': variant.sku,
        })

    return JsonResponse({'variants': results})



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
        wishlist_session = request.session.get('wishlist', [])
        wishlist_count = len(wishlist_session)

    return JsonResponse({
        'cart_count': cart_count,
        'wishlist_count': wishlist_count,
    })




# --- Wishlist Views ---
def wishlist_view(request):
    """Displays the user's wishlist with pagination."""
    products_qs = Product.objects.none()
    products_in_wishlist_ids = set()
    if request.user.is_authenticated:
        try:
            wishlist = request.user.wishlist
            products_qs = Product.objects.filter(
                wishlistitem__wishlist=wishlist
            ).select_related(
                'category', 'subcategory', 'brand'
            ).prefetch_related('images').order_by('name')
            products_in_wishlist_ids = set(
                wishlist.items.values_list('product_id', flat=True)
            )
        except Wishlist.DoesNotExist:
            products_qs = Product.objects.none()
            products_in_wishlist_ids = set()
    else:
        wishlist_session = request.session.get('wishlist', [])
        if wishlist_session:
            products_qs = Product.objects.filter(id__in=wishlist_session).select_related(
                'category', 'subcategory', 'brand'
            ).prefetch_related('images').order_by('name')
            products_in_wishlist_ids = set(wishlist_session)
        else:
            products_qs = Product.objects.none()
            products_in_wishlist_ids = set()

    # Pagination: 8 products per page
    paginator = Paginator(products_qs, 8)
    page = request.GET.get('page', 1)
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    # Update wishlist count in session
    request.session['wishlist_count'] = products_qs.count()

    context = {
        'products': products,
        'products_in_wishlist_ids': products_in_wishlist_ids,
    }
    return render(request, 'shop/wishlist_view.html', context)


@require_POST
def add_to_cart(request):
    # Determine current language
    lang = getattr(request, 'LANGUAGE_CODE', 'en')

    try:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = request.POST
        product_variant_id = data.get('product_variant_id')
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
    except (ValueError, TypeError):
        message = 'Invalid data provided.' if lang == 'en' else 'بيانات غير صالحة.'
        return JsonResponse({'success': False, 'message': message}, status=400)

    product_variant = None
    product = None
    if product_variant_id:
        try:
            product_variant = ProductVariant.objects.get(id=product_variant_id, is_available=True)
            product = product_variant.product
        except ProductVariant.DoesNotExist:
            message = 'Product variant not found or not available.' if lang == 'en' else 'النسخة المحددة من المنتج غير موجودة أو غير متوفرة.'
            return JsonResponse({'success': False, 'message': message}, status=404)
    elif product_id:
        try:
            product = Product.objects.get(id=product_id, is_active=True, is_available=True)
            product_variant = ProductVariant.objects.filter(
                product=product, is_available=True, stock_quantity__gt=0
            ).order_by('pk').first()
            if not product_variant:
                message = f'No available variants for {product.name} or out of stock.' if lang == 'en' else f'لا توجد نسخ متاحة لـ {product.name} أو نفدت الكمية.'
                return JsonResponse({'success': False, 'message': message}, status=400)
        except Product.DoesNotExist:
            message = 'Product not found or not available.' if lang == 'en' else 'المنتج غير موجود أو غير متوفر.'
            return JsonResponse({'success': False, 'message': message}, status=404)
    else:
        message = 'Product or variant not provided.' if lang == 'en' else 'لم يتم تقديم منتج أو نسخة.'
        return JsonResponse({'success': False, 'message': message}, status=400)

    if quantity <= 0:
        message = 'Quantity must be at least 1.' if lang == 'en' else 'يجب أن تكون الكمية على الأقل 1.'
        return JsonResponse({'success': False, 'message': message}, status=400)

    if product_variant.stock_quantity < quantity:
        message = (
            f'Not enough stock for {product.name} ({product_variant.color.name if product_variant.color else "N/A"}, '
            f'{product_variant.size.name if product_variant.size else "N/A"}). Available: {product_variant.stock_quantity}.'
        ) if lang == 'en' else (
            f'الكمية غير كافية للمنتج {product.name} ({product_variant.color.name if product_variant.color else "غير متوفر"}, '
            f'{product_variant.size.name if product_variant.size else "غير متوفر"}). المتوفر: {product_variant.stock_quantity}.'
        )
        return JsonResponse({'success': False, 'message': message}, status=400)

    with transaction.atomic():
        if request.user.is_authenticated:
            cart, created = Cart.objects.select_for_update().get_or_create(user=request.user)
        else:
            session_key = request.session.session_key
            if not session_key:
                request.session.save()
                session_key = request.session.session_key
            cart, created = Cart.objects.select_for_update().get_or_create(session_key=session_key)

        cart_item, created = CartItem.objects.select_for_update().get_or_create(
            cart=cart,
            product_variant=product_variant,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        request.session['cart_count'] = cart.total_items
        message = 'Item added to cart successfully!' if lang == 'en' else 'تمت إضافة العنصر إلى السلة بنجاح!'
        return JsonResponse({'success': True, 'message': message, 'cart_total_items': cart.total_items})

@require_POST
def add_to_wishlist(request):
    lang = getattr(request, 'LANGUAGE_CODE', 'en')
    try:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON.' if lang == 'en' else 'نص غير صالح.'}, status=400)
        product_id = data.get('product_id')
        if not product_id:
            return JsonResponse({'success': False, 'message': 'Product ID not provided.' if lang == 'en' else 'معرف المنتج غير موجود.'}, status=400)
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Product not found.' if lang == 'en' else 'المنتج غير موجود.'}, status=404)

        if request.user.is_authenticated:
            with transaction.atomic():
                wishlist, created = Wishlist.objects.select_for_update().get_or_create(user=request.user)
                wishlist_item, item_created = WishlistItem.objects.get_or_create(wishlist=wishlist, product=product)
                if item_created:
                    message = 'Item added to wishlist successfully!' if lang == 'en' else 'تمت إضافة العنصر إلى قائمة الرغبات بنجاح!'
                    status = 'added'
                else:
                    message = 'Item is already in your wishlist.' if lang == 'en' else 'العنصر موجود بالفعل في قائمة رغباتك.'
                    status = 'exists'
                wishlist_count = wishlist.items.count()
        else:
            wishlist_session = request.session.get('wishlist', [])
            if str(product_id) in wishlist_session:
                message = 'Item is already in your wishlist.' if lang == 'en' else 'العنصر موجود بالفعل في قائمة رغباتك.'
                status = 'exists'
            else:
                wishlist_session.append(str(product_id))
                request.session['wishlist'] = wishlist_session
                message = 'Item added to wishlist successfully!' if lang == 'en' else 'تمت إضافة العنصر إلى قائمة الرغبات بنجاح!'
                status = 'added'
            wishlist_count = len(wishlist_session)

        request.session['wishlist_count'] = wishlist_count
        return JsonResponse({'success': True, 'message': message, 'status': status, 'wishlist_total_items': wishlist_count})
    except Exception:
        message = 'An error occurred.' if lang == 'en' else 'حدث خطأ.'
        return JsonResponse({'success': False, 'message': message}, status=500)

@require_POST
def remove_from_wishlist(request):
    lang = getattr(request, 'LANGUAGE_CODE', 'en')
    try:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON.' if lang == 'en' else 'نص غير صالح.'}, status=400)
        product_id = data.get('product_id')
        if not product_id:
            return JsonResponse({'success': False, 'message': 'Product ID not provided.' if lang == 'en' else 'معرف المنتج غير موجود.'}, status=400)
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Product not found.' if lang == 'en' else 'المنتج غير موجود.'}, status=404)

        if request.user.is_authenticated:
            try:
                wishlist = Wishlist.objects.get(user=request.user)
            except Wishlist.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Wishlist not found for user.', 'status': 'wishlist_missing'}, status=404)
            with transaction.atomic():
                deleted_count, _ = WishlistItem.objects.filter(wishlist=wishlist, product=product).delete()
                if deleted_count > 0:
                    wishlist_count = wishlist.items.count()
                    request.session['wishlist_count'] = wishlist_count
                    message = 'Item removed successfully!' if lang == 'en' else 'تمت إزالة العنصر بنجاح!'
                    return JsonResponse({'success': True, 'message': message, 'wishlist_total_items': wishlist_count, 'status': 'removed'})
                else:
                    message = 'Item not found in wishlist.' if lang == 'en' else 'العنصر غير موجود في قائمة الرغبات.'
                    return JsonResponse({'success': False, 'message': message, 'status': 'not_found'}, status=404)
        else:
            wishlist_session = request.session.get('wishlist', [])
            if str(product_id) in wishlist_session:
                wishlist_session.remove(str(product_id))
                request.session['wishlist'] = wishlist_session
                wishlist_count = len(wishlist_session)
                request.session['wishlist_count'] = wishlist_count
                message = 'Item removed successfully!' if lang == 'en' else 'تمت إزالة العنصر بنجاح!'
                return JsonResponse({'success': True, 'message': message, 'wishlist_total_items': wishlist_count, 'status': 'removed'})
            else:
                message = 'Item not found in wishlist.' if lang == 'en' else 'العنصر غير موجود في قائمة الرغبات.'
                return JsonResponse({'success': False, 'message': message, 'status': 'not_found'}, status=404)
    except Exception:
        message = 'An error occurred.' if lang == 'en' else 'حدث خطأ.'
        return JsonResponse({'success': False, 'message': message}, status=500)

@require_POST
def remove_from_cart(request):
    lang = getattr(request, 'LANGUAGE_CODE', 'en')
    try:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON.' if lang == 'en' else 'نص غير صالح.'}, status=HttpResponseBadRequest.status_code)
        cart_item_id = data.get('cart_item_id')
        if not cart_item_id:
            return JsonResponse({'success': False, 'message': 'Cart item ID not provided.' if lang == 'en' else 'معرف عنصر السلة غير موجود.'}, status=HttpResponseBadRequest.status_code)
        try:
            cart_item_id = int(cart_item_id)
        except ValueError:
            return JsonResponse({'success': False, 'message': 'Invalid cart item ID format.' if lang == 'en' else 'تنسيق معرف عنصر السلة غير صالح.'}, status=HttpResponseBadRequest.status_code)
        try:
            cart_item = get_object_or_404(CartItem.objects.select_related('cart'), id=cart_item_id)
            if request.user.is_authenticated:
                if cart_item.cart.user != request.user:
                    return JsonResponse({'success': False, 'message': 'Unauthorized action.' if lang == 'en' else 'إجراء غير مصرح به.'}, status=HttpResponseForbidden.status_code)
            else:
                if cart_item.cart.session_key != request.session.session_key:
                    return JsonResponse({'success': False, 'message': 'Unauthorized action.' if lang == 'en' else 'إجراء غير مصرح به.'}, status=HttpResponseForbidden.status_code)
            cart = cart_item.cart
            with transaction.atomic():
                cart_item.delete()
                request.session['cart_count'] = cart.total_items
                message = 'Item removed from cart.' if lang == 'en' else 'تمت إزالة العنصر من السلة.'
                return JsonResponse({
                    'success': True,
                    'message': message,
                    'cart_item_id': cart_item_id,
                    'cart_total_items': cart.total_items,
                    'cart_total_price': str(cart.total_price)
                })
        except CartItem.DoesNotExist:
            message = 'Cart item not found.' if lang == 'en' else 'لم يتم العثور على عنصر في السلة.'
            return JsonResponse({'success': False, 'message': message}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'An unexpected error occurred: {str(e)}'}, status=500)
    except Exception:
        message = 'An error occurred.' if lang == 'en' else 'حدث خطأ.'
        return JsonResponse({'success': False, 'message': message}, status=500)

# --- Cart Views ---
def cart_view(request):
    cart_items_data = []
    total_cart_price = Decimal('0.00')
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
            'product_variant__product', 'product_variant__color', 'product_variant__size'
        ).order_by('pk')

        for item in cart_items:
            current_stock = item.product_variant.stock_quantity if item.product_variant else 0
            if item.quantity > current_stock:
                item.quantity = current_stock
                item.save()

            if current_stock == 0:
                item.delete()
                continue

            item_total = item.get_total_price()
            total_cart_price += item_total
            cart_items_data.append({
                'id': item.id,
                'variant': item.product_variant,
                'quantity': item.quantity,
                'total': item_total,
                'stock_available': current_stock
            })

        cart.update_totals()
        total_cart_price = cart.total_price_field
        request.session['cart_count'] = cart.total_items_field
    else:
        request.session['cart_count'] = 0

    grand_total = total_cart_price + shipping_fee

    return render(request, 'shop/cart_view.html', {
        'items': cart_items_data,
        'total': total_cart_price,
        'shipping_fee': shipping_fee,
        'grand_total': grand_total,
        'cart': cart
    })
@require_POST
def update_cart_quantity(request):
    try:
        lang = getattr(request, 'LANGUAGE_CODE', 'en')  # Default to 'en' if not set
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            message = 'Invalid JSON.' if lang == 'en' else 'نص غير صالح.'
            return JsonResponse({'success': False, 'message': message}, status=HttpResponseBadRequest.status_code)

        cart_item_id = data.get('cart_item_id')
        new_quantity = data.get('quantity')

        if not cart_item_id or new_quantity is None:
            message = 'Cart item ID or quantity not provided.' if lang == 'en' else 'معرف عنصر السلة أو الكمية غير موجود.'
            return JsonResponse({'success': False, 'message': message}, status=HttpResponseBadRequest.status_code)

        try:
            cart_item_id = int(cart_item_id)
            new_quantity = int(new_quantity)
        except ValueError:
            message = 'Invalid quantity or item ID format.' if lang == 'en' else 'تنسيق معرف العنصر أو الكمية غير صالح.'
            return JsonResponse({'success': False, 'message': message}, status=HttpResponseBadRequest.status_code)

        try:
            cart_item = get_object_or_404(CartItem.objects.select_related('cart', 'product_variant'), id=cart_item_id)
            if request.user.is_authenticated:
                if cart_item.cart.user != request.user:
                    message = 'Unauthorized action.' if lang == 'en' else 'إجراء غير مصرح به.'
                    return JsonResponse({'success': False, 'message': message}, status=HttpResponseForbidden.status_code)
            else:
                if cart_item.cart.session_key != request.session.session_key:
                    message = 'Unauthorized action.' if lang == 'en' else 'إجراء غير مصرح به.'
                    return JsonResponse({'success': False, 'message': message}, status=HttpResponseForbidden.status_code)

            if new_quantity <= 0:
                with transaction.atomic():
                    cart_item.delete()
                message = 'Item removed from cart.' if lang == 'en' else 'تمت إزالة العنصر من السلة.'
                status = 'removed'
                item_total_price = Decimal('0.00')
            else:
                if cart_item.product_variant.stock_quantity < new_quantity:
                    new_quantity = cart_item.product_variant.stock_quantity
                with transaction.atomic():
                    cart_item.quantity = new_quantity
                    cart_item.save()
                message = 'Cart quantity updated.' if lang == 'en' else 'تم تحديث كمية السلة.'
                status = 'updated'
                item_total_price = cart_item.get_total_price()

            request.session['cart_count'] = cart_item.cart.total_items
            return JsonResponse({
                'success': True,
                'message': message,
                'status': status,
                'cart_item_id': cart_item_id,
                'new_quantity': cart_item.quantity if status == 'updated' else 0,
                'item_total_price': str(item_total_price),
                'cart_total_items': cart_item.cart.total_items,
                'cart_total_price': str(cart_item.cart.total_price)
            })

        except CartItem.DoesNotExist:
            message = 'Cart item not found.' if lang == 'en' else 'لم يتم العثور على عنصر في السلة.'
            return JsonResponse({'success': False, 'message': message}, status=404)

        except Exception as e:
            print(f"Error updating cart quantity: {e}")
            message = f'An unexpected error occurred: {str(e)}' if lang == 'en' else f'حدث خطأ غير متوقع: {str(e)}'
            return JsonResponse({'success': False, 'message': message}, status=500)

    except Exception as e:
        message = 'An error occurred.' if lang == 'en' else 'حدث خطأ.'
        return JsonResponse({'success': False, 'message': message}, status=500)


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
        messages.warning(request, _("Your cart is empty. Please add items before checking out."))
        return redirect('shop:cart_view')

    cart.update_totals()
    if cart.total_items == 0:
        messages.warning(request, _("Your cart is empty after stock adjustments. Please add items before checking out."))
        return redirect('shop:cart_view')

    initial_shipping_data = {}
    user_shipping_addresses = ShippingAddress.objects.none()

    if request.user.is_authenticated:
        user_orders = Order.objects.filter(user=request.user)
        user_shipping_addresses = ShippingAddress.objects.filter(order__in=user_orders)
        if user_shipping_addresses.exists():
            default_address = user_shipping_addresses.filter(is_default=True).first() or user_shipping_addresses.order_by('-id').first()
            if default_address:
                initial_shipping_data = {
                    'full_name': default_address.full_name,
                    'address_line1': default_address.address_line1,
                    'address_line2': default_address.address_line2,
                    'city': default_address.city,
                    'email': default_address.email,
                    'phone_number': default_address.phone_number,
                }

    shipping_form = ShippingAddressForm(request.POST or None, initial=initial_shipping_data)
    payment_form = PaymentForm(request.POST or None)

    shipping_fee = Decimal(config.SHIPPING_RATE_CAIRO)  # <-- Add this
    if request.method == 'POST':
        selected_address_id = request.POST.get('selected_address')
        if selected_address_id == 'new' or not user_shipping_addresses.exists():
            # New address or no saved addresses
            if shipping_form.is_valid() and payment_form.is_valid():
                return process_order(request, cart, shipping_form, payment_form)
            else:
                messages.error(request, _("Please correct the errors in your shipping and/or payment details."))
        else:
            # Existing address selected
            if not request.user.is_authenticated:
                messages.error(request, _("You must be logged in to use an existing address."))
                return redirect('shop:checkout')
            try:
                selected_address = get_object_or_404(ShippingAddress, id=selected_address_id, order__user=request.user)
            except ShippingAddress.DoesNotExist:
                messages.error(request, _("Selected shipping address not found or does not belong to you."))
                return redirect('shop:checkout')

            if payment_form.is_valid():
                return process_order(request, cart, payment_form=payment_form, existing_address=selected_address)
            else:
                messages.error(request, _("Please correct the errors in your payment details."))

    context = {
        'cart': cart,
        'shipping_form': shipping_form,
        'payment_form': payment_form,
        'user_shipping_addresses': user_shipping_addresses,
        'shipping_fee': shipping_fee,  # <-- Pass to template
        'grand_total': cart.total_price_field + shipping_fee  # <-- Optional precomputed total
    }
    return render(request, 'shop/checkout.html', context)

@transaction.atomic
def process_order(request, cart, shipping_form=None, payment_form=None, existing_address=None):
    try:
        if not shipping_form and not existing_address:
            messages.error(request, _("Shipping information is required."))
            return redirect('shop:checkout')

        if not payment_form:
            messages.error(request, _("Payment information is required."))
            return redirect('shop:checkout')

        # Create order
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            full_name=shipping_form.cleaned_data['full_name'] if shipping_form else existing_address.full_name,
            email=request.user.email if request.user.is_authenticated else '',  # Optional
            phone_number=shipping_form.cleaned_data['phone_number'] if shipping_form else existing_address.phone_number,
            subtotal=Decimal('0.00'),
            shipping_cost=Decimal(config.SHIPPING_RATE_CAIRO),  # Using your config
            grand_total=Decimal('0.00'),
            status='pending',
            payment_status='pending',
        )

        # Save shipping address
        if existing_address:
            shipping_address = existing_address
            shipping_address.order = order
            shipping_address.save()
        else:
            shipping_address = shipping_form.save(commit=False)
            if hasattr(shipping_address, 'user') and request.user.is_authenticated:
                shipping_address.user = request.user
            shipping_address.order = order
            shipping_address.save()

        order.shipping_address = shipping_address
        order.save()

        # Create payment
        payment_data = payment_form.cleaned_data
        payment = Payment.objects.create(
            order=order,
            payment_method=payment_data.get('payment_method'),
            amount=Decimal('0.00'),  # Will update later
            transaction_id=f"TXN-{uuid.uuid4().hex[:10]}",
            is_success=False,
        )

        # Process cart items
        subtotal = Decimal('0.00')
        for cart_item in cart.items.select_related('product_variant').all():
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
                price_at_purchase=price
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
        order.status = 'processing'
        order.payment_status = 'paid'
        order.save()

        # Clear cart
        cart.items.all().delete()
        cart.update_totals()
        if not request.user.is_authenticated:
            cart.delete()
        request.session['cart_count'] = 0

        messages.success(request, _(f"Your order {order.order_number} has been placed successfully!"))
        return redirect('shop:order_confirmation', order_number=order.order_number)

    except ValueError as e:
        messages.error(request, _(f"Order failed: {e}"))
        return redirect('shop:checkout')
    except Exception as e:
        logger.exception(f"Order processing failed for user {request.user}: {e}")
        messages.error(request, _(f"An unexpected error occurred during checkout: {e}"))
        return redirect('shop:checkout')

def order_confirmation(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)

    if order.user != request.user and order.user is not None:
        return render(request, 'shop/order_not_found.html', status=403)

    order_items = order.items.select_related(
        'product_variant__product',
        'product_variant__color',
        'product_variant__size'
    )

    return render(request, 'shop/order_confirmation.html', {
        'order': order,
        'order_items': order_items
    })

def order_detail(request, order_number):
    if request.user.is_authenticated:
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
    else:
        order = get_object_or_404(Order, order_number=order_number, user=None)
    order_items = order.items.select_related(
        'product_variant__product', 'product_variant__color', 'product_variant__size'
    ).all()
    return render(request, 'shop/order_detail.html', {'order': order, 'order_items': order_items})


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'shop/order_history.html', {'orders': page_obj})

def get_available_sizes_ajax(request):
    """
    AJAX endpoint to get available sizes based on product and selected color.
    """
    if request.method == 'GET' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        product_id = request.GET.get('product_id')
        color_id = request.GET.get('color_id')

        product = get_object_or_404(Product, id=product_id)
        available_sizes_query = product.get_available_sizes(color_id=color_id)

        # Convert queryset to a list of dictionaries for JSON response
        available_sizes_data = list(available_sizes_query.values('id', 'name'))

        return JsonResponse({'success': True, 'available_sizes': available_sizes_data})
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

def vendor_detail(request, slug):
    # 1. Get the VendorProfile instance
    vendor_profile = get_object_or_404(VendorProfile, slug=slug)

    # 2. Access the related MnoryUser instance from the VendorProfile
    # As per your models.py, VendorProfile has a OneToOneField named 'user'
    # which points to settings.AUTH_USER_MODEL (your MnoryUser).
    vendor_user_instance = vendor_profile.user

    # Get products for this vendor, filtered by the MnoryUser instance
    products_queryset = Product.objects.filter(vendor=vendor_user_instance, is_active=True)

    # Apply filters
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    category_id = request.GET.get('category')
    brand_id = request.GET.get('brand')
    colors_ids = request.GET.getlist('colors') # request.GET.getlist returns a list of selected IDs
    sizes_ids = request.GET.getlist('sizes')   # request.GET.getlist returns a list of selected IDs
    sort_by = request.GET.get('sort', '-created_at') # Default sort to newest first

    # Apply price filters
    if price_min:
        products_queryset = products_queryset.filter(price__gte=price_min)
    if price_max:
        products_queryset = products_queryset.filter(price__lte=price_max)

    # Apply category filter
    if category_id:
        products_queryset = products_queryset.filter(category_id=category_id)

    # Apply brand filter
    if brand_id:
        products_queryset = products_queryset.filter(brand_id=brand_id)

    # Apply colors filter (ManyToManyField through ProductColor)
    if colors_ids:
        # Filter products that have at least one of the selected colors through the ProductColor intermediate model
        products_queryset = products_queryset.filter(productcolor__color__id__in=colors_ids).distinct()

    # Apply sizes filter (ManyToManyField through ProductSize)
    if sizes_ids:
        # Filter products that have at least one of the selected sizes through the ProductSize intermediate model
        products_queryset = products_queryset.filter(productsize__size__id__in=sizes_ids).distinct()

    # Apply sorting
    products_queryset = products_queryset.order_by(sort_by)

    # Pagination
    paginator = Paginator(products_queryset, 9) # Show 9 products per page
    page = request.GET.get('page')
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
    categories = Category.objects.filter(products__vendor=vendor_user_instance, products__is_active=True).distinct()
    
    # Filter Brands that have active products from this vendor
    brands = Brand.objects.filter(products__vendor=vendor_user_instance, products__is_active=True).distinct()
    
    # Filter Colors that are associated with active products from this vendor via ProductColor
    colors = Color.objects.filter(productcolor__product__vendor=vendor_user_instance, productcolor__product__is_active=True).distinct()
    
    # Filter Sizes that are associated with active products from this vendor via ProductSize
    sizes = Size.objects.filter(productsize__product__vendor=vendor_user_instance, productsize__product__is_active=True).distinct()

    # Get min/max price for the vendor's products (for filter range)
    price_range = Product.objects.filter(vendor=vendor_user_instance, is_active=True).aggregate(Min('price'), Max('price'))
    # Ensure price_range has a default if no products exist
    min_price_val = price_range['price__min'] if price_range['price__min'] is not None else 0
    max_price_val = price_range['price__max'] if price_range['price__max'] is not None else 0

    # Vendor stats
    vendor_stats = {
        'total_products': Product.objects.filter(vendor=vendor_user_instance, is_active=True).count(),
        # Count categories that have active products from this vendor
        'categories_count': categories.count(), # We already filtered `categories` above
    }

    context = {
        'vendor': vendor_profile, # Pass the VendorProfile instance to the template
        'products': products_page,
        'categories': categories,
        'brands': brands,
        'colors': colors,
        'sizes': sizes,
        'price_range': {'price__min': min_price_val, 'price__max': max_price_val}, # Pass adjusted price_range
        'vendor_stats': vendor_stats,
    }
    return render(request, 'shop/vendor_detail.html', context)