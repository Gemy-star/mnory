# shop/views.py

from django.shortcuts import render, get_object_or_404 , redirect
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Min, Max
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt # Use for simplicity, but in production use csrf_token in form/ajax
from django.contrib.auth.decorators import login_required # For wishlist (requires logged-in user)
from django.contrib.auth import authenticate, login
from .forms import RegisterForm, LoginForm
from .models import (
    Category, SubCategory, FitType, Brand, Color, Size,
    Product, ProductVariant, Cart, CartItem, Wishlist, WishlistItem,MnoryUser , VendorProfile
)
from django.views.decorators.http import require_POST


def get_filtered_products(request, base_queryset):
    filters = {
        'subcategory': request.GET.get('subcategory_slug'),
        'vendor': request.GET.get('vendor'),
        'fit_type': request.GET.get('fit_type'),
        'brand': request.GET.get('brand'),
        'color': request.GET.get('color'),
        'size': request.GET.get('size'),
        'min_price': request.GET.get('min_price'),
        'max_price': request.GET.get('max_price'),
        'sort': request.GET.get('sort'),
        'is_best_seller': request.GET.get('is_best_seller'),
        'is_new_arrival': request.GET.get('is_new_arrival'),
        'is_on_sale': request.GET.get('is_on_sale'),
    }

    queryset = base_queryset

    if filters['subcategory']:
        queryset = queryset.filter(subcategory__slug=filters['subcategory'])

    if filters['vendor']:
        queryset = queryset.filter(vendor__id=filters['vendor'])

    if filters['fit_type']:
        queryset = queryset.filter(fit_type__slug=filters['fit_type'])

    if filters['brand']:
        queryset = queryset.filter(brand__slug=filters['brand'])

    if filters['color']:
        queryset = queryset.filter(variants__color__name=filters['color']).distinct()

    if filters['size']:
        queryset = queryset.filter(variants__size__name=filters['size']).distinct()

    if filters['min_price']:
        try:
            queryset = queryset.filter(price__gte=float(filters['min_price']))
        except ValueError:
            pass

    if filters['max_price']:
        try:
            queryset = queryset.filter(price__lte=float(filters['max_price']))
        except ValueError:
            pass

    if filters['is_best_seller'] in ['1', 'true']:
        queryset = queryset.filter(is_best_seller=True)

    if filters['is_new_arrival'] in ['1', 'true']:
        queryset = queryset.filter(is_new_arrival=True)

    if filters['is_on_sale'] in ['1', 'true']:
        queryset = queryset.filter(is_on_sale=True)

    # Sorting
    if filters['sort'] == 'price_low':
        queryset = queryset.order_by('price')
    elif filters['sort'] == 'price_high':
        queryset = queryset.order_by('-price')
    elif filters['sort'] == 'newest':
        queryset = queryset.order_by('-created_at')
    elif filters['sort'] == 'popular':
        queryset = queryset.order_by('-popularity')  # Ensure this field exists
    else:
        queryset = queryset.order_by('name')

    return queryset, filters


def category_detail(request, slug):
    category = None
    subcategory = None
    subcategories = []
    base_queryset = Product.objects.filter(is_active=True, is_available=True)

    # Detect if it's a subcategory
    try:
        subcategory = SubCategory.objects.select_related('category').get(slug=slug, is_active=True)
        category = subcategory.category
        base_queryset = base_queryset.filter(subcategory=subcategory)
    except SubCategory.DoesNotExist:
        category = get_object_or_404(Category, slug=slug, is_active=True)
        base_queryset = base_queryset.filter(category=category)
        subcategories = category.subcategories.filter(is_active=True)

    # Filter products via helper
    filtered_queryset, filters = get_filtered_products(request, base_queryset)

    # Pagination
    paginator = Paginator(filtered_queryset, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Sidebar options
    fit_types = FitType.objects.filter(is_active=True)
    brands = Brand.objects.filter(is_active=True)
    colors = Color.objects.filter(is_active=True)
    sizes = Size.objects.filter(is_active=True)
    vendors = VendorProfile.objects.filter(is_approved=True, user__is_active=True)
    categories = Category.objects.filter(is_active=True)

    # Price range
    price_range = base_queryset.aggregate(Min('price'), Max('price'))

    context = {
        'category': category,
        'subcategory': subcategory,
        'subcategories': subcategories,
        'products': page_obj,
        'fit_types': fit_types,
        'brands': brands,
        'colors': colors,
        'sizes': sizes,
        'vendors': vendors,
        'categories': categories,
        'price_range': price_range,
        'current_filters': filters,
    }

    return render(request, 'shop/category_detail.html', context)


def home(request):
    """Homepage view"""
    featured_products = Product.objects.filter(
        is_featured=True,
        is_active=True,
        is_available=True
    ).select_related('category', 'subcategory', 'brand')[:8]

    new_arrivals = Product.objects.filter(
        is_new_arrival=True,
        is_active=True,
        is_available=True
    ).select_related('category', 'subcategory', 'brand')[:8]

    best_sellers = Product.objects.filter(
        is_best_seller=True,
        is_active=True,
        is_available=True
    ).select_related('category', 'subcategory', 'brand')[:8]

    sale_products = Product.objects.filter(
        is_on_sale=True,
        is_active=True,
        is_available=True
    ).select_related('category', 'subcategory', 'brand')[:8]

    categories = Category.objects.filter(is_active=True)

    context = {
        'featured_products': featured_products,
        'new_arrivals': new_arrivals,
        'best_sellers': best_sellers,
        'sale_products': sale_products,
        'categories': categories,
    }

    return render(request, 'shop/home.html', context)



def subcategory_detail(request, category_slug, slug):
    """Display subcategory detail page with filtering, sorting, and pagination."""

    category = get_object_or_404(Category, slug=category_slug, is_active=True)
    subcategory = get_object_or_404(SubCategory, slug=slug, category=category, is_active=True)

    # Initial product queryset
    products = Product.objects.filter(
        subcategory=subcategory,
        is_active=True,
        is_available=True
    ).select_related('category', 'subcategory', 'brand').prefetch_related('colors', 'sizes')

    # Filters
    filters = {
        'subcategory__slug': request.GET.get('subcategory'),
        'fit_type__slug': request.GET.get('fit_type'),
        'brand__slug': request.GET.get('brand'),
        'colors__name__icontains': request.GET.get('color'),
        'sizes__name__icontains': request.GET.get('size'),
    }

    # Apply non-empty filters
    for field, value in filters.items():
        if value:
            products = products.filter(**{field: value})

    # Price filters
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # Sorting
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'popular':
        products = products.order_by('-is_best_seller', '-created_at')
    else:
        products = products.order_by('name')

    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Filter option sets
    fit_types = FitType.objects.filter(is_active=True)
    brands = Brand.objects.filter(is_active=True)
    colors = Color.objects.filter(is_active=True)
    sizes = Size.objects.filter(is_active=True)
    all_categories = Category.objects.filter(is_active=True)

    # Price range for this subcategory
    price_range = Product.objects.filter(
        subcategory=subcategory,
        is_active=True,
        is_available=True
    ).aggregate(min_price=Min('price'), max_price=Max('price'))

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
        'subcategories': category.subcategories.filter(is_active=True),
        'current_filters': {
            'subcategory': request.GET.get('subcategory', ''),
            'fit_type': request.GET.get('fit_type', ''),
            'brand': request.GET.get('brand', ''),
            'color': request.GET.get('color', ''),
            'size': request.GET.get('size', ''),
            'min_price': min_price or '',
            'max_price': max_price or '',
            'sort': sort_by,
        }
    }

    return render(request, 'shop/subcategory_detail.html', context)

def product_detail(request, slug):
    """Product detail view"""
    product = get_object_or_404(
        Product.objects.select_related('category', 'subcategory', 'brand', 'fit_type'),
        slug=slug,
        is_active=True,
        is_available=True
    )

    # Get related products
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True,
        is_available=True
    ).exclude(id=product.id)[:8]

    # Get product variants
    variants = ProductVariant.objects.filter(product=product, is_available=True)

    # Get available colors and sizes
    available_colors = product.get_available_colors()
    available_sizes = product.get_available_sizes()

    # Get product images
    product_images = product.images.all()

    # Pass all categories for the base.html navbar
    categories = Category.objects.filter(is_active=True)

    context = {
        'product': product,
        'related_products': related_products,
        'variants': variants,
        'available_colors': available_colors,
        'available_sizes': available_sizes,
        'product_images': product_images,
        'categories': categories, # Pass categories for base.html dropdown
    }

    return render(request, 'shop/product_detail.html', context)

@require_http_methods(["GET"])
def search_products(request):
    """AJAX search for products"""
    query = request.GET.get('q', '')

    if len(query) < 2:
        return JsonResponse({'products': []})

    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query) |
        Q(brand__name__icontains=query) |
        Q(category__name__icontains=query),
        is_active=True,
        is_available=True
    ).select_related('category', 'subcategory', 'brand')[:10]

    results = []
    for product in products:
        main_image = product.get_main_image()
        results.append({
            'id': product.id,
            'name': product.name,
            'price': str(product.get_price),
            'url': product.get_absolute_url(),
            'image': main_image.image.url if main_image else '',
            'category': product.category.name,
            'brand': product.brand.name if product.brand else '',
        })

    return JsonResponse({'products': results})

@require_http_methods(["GET"])
def get_product_variants(request, product_id):
    """Get product variants for AJAX"""
    product = get_object_or_404(Product, id=product_id)
    color_id = request.GET.get('color')
    size_id = request.GET.get('size')

    variants = ProductVariant.objects.filter(product=product, is_available=True)

    if color_id:
        variants = variants.filter(color_id=color_id)

    if size_id:
        variants = variants.filter(size_id=size_id)

    results = []
    for variant in variants:
        results.append({
            'id': variant.id,
            'color': variant.color.name,
            'size': variant.size.name,
            'price': str(variant.get_price),
            'stock': variant.stock_quantity,
            'sku': variant.sku,
        })

    return JsonResponse({'variants': results})

@require_http_methods(["POST"])
@csrf_exempt # For simplicity, but in production use csrf_token in form/ajax
def add_to_cart(request):
    """AJAX view to add a product variant to the cart."""
    product_variant_id = request.POST.get('product_variant_id')
    quantity = int(request.POST.get('quantity', 1))

    if not product_variant_id:
        return JsonResponse({'success': False, 'message': 'Product variant not provided.'}, status=400)

    try:
        product_variant = get_object_or_404(ProductVariant, id=product_variant_id)

        if quantity <= 0:
            return JsonResponse({'success': False, 'message': 'Quantity must be at least 1.'}, status=400)

        if product_variant.stock_quantity < quantity:
            return JsonResponse({'success': False, 'message': 'Not enough stock available.'}, status=400)

        # Get or create cart
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
        else:
            session_key = request.session.session_key
            if not session_key:
                request.session.save()
                session_key = request.session.session_key
            cart, created = Cart.objects.get_or_create(session_key=session_key)

        # Add or update cart item
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product_variant=product_variant,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        return JsonResponse({'success': True, 'message': 'Item added to cart successfully!', 'cart_total_items': cart.total_items})

    except ProductVariant.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Product variant not found.'}, status=404)
    except ValueError:
        return JsonResponse({'success': False, 'message': 'Invalid quantity.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'}, status=500)

@require_http_methods(["POST"])
@login_required # User must be logged in to add to wishlist
@csrf_exempt # For simplicity, but in production use csrf_token in form/ajax
def add_to_wishlist(request):
    """AJAX view to add a product to the wishlist."""
    product_id = request.POST.get('product_id')

    if not product_id:
        return JsonResponse({'success': False, 'message': 'Product not provided.'}, status=400)

    try:
        product = get_object_or_404(Product, id=product_id)

        wishlist, created = Wishlist.objects.get_or_create(user=request.user)

        wishlist_item, created = WishlistItem.objects.get_or_create(
            wishlist=wishlist,
            product=product
        )

        if created:
            message = 'Item added to wishlist successfully!'
        else:
            message = 'Item is already in your wishlist.'

        return JsonResponse({'success': True, 'message': message})

    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Product not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'}, status=500)

@require_http_methods(["GET"])
def get_cart_and_wishlist_counts(request):
    """AJAX view to get current cart item count and wishlist item count."""
    cart_total_items = 0
    wishlist_total_items = 0

    # Get cart count
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_total_items = cart.total_items
        except Cart.DoesNotExist:
            pass
    else:
        session_key = request.session.session_key
        if session_key:
            try:
                cart = Cart.objects.get(session_key=session_key)
                cart_total_items = cart.total_items
            except Cart.DoesNotExist:
                pass

    # Get wishlist count (only for authenticated users)
    if request.user.is_authenticated:
        try:
            wishlist = Wishlist.objects.get(user=request.user)
            wishlist_total_items = wishlist.items.count()
        except Wishlist.DoesNotExist:
            pass

    return JsonResponse({
        'cart_total_items': cart_total_items,
        'wishlist_total_items': wishlist_total_items
    })


def account_view(request):
    login_form = LoginForm(request, data=request.POST or None)
    register_form = RegisterForm(request.POST or None)

    if 'login' in request.POST and login_form.is_valid():
        user = authenticate(
            request,
            username=login_form.cleaned_data['username'],
            password=login_form.cleaned_data['password']
        )
        if user:
            login(request, user)
            return redirect('home')  # or wherever

    elif 'register' in request.POST and register_form.is_valid():
        user = register_form.save()
        login(request, user)
        return redirect('home')

    return render(request, 'shop/account.html', {
        'login_form': login_form,
        'register_form': register_form
    })


def get_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key or request.session.save() or request.session.session_key
        cart, _ = Cart.objects.get_or_create(session_key=session_key)
    return cart


def cart_detail(request):
    cart = get_cart(request)
    return render(request, 'cart/cart_detail.html', {'cart': cart})


@require_POST
def add_to_cart(request):
    cart = get_cart(request)
    variant_id = request.POST.get('variant_id')
    quantity = int(request.POST.get('quantity', 1))
    variant = get_object_or_404(ProductVariant, id=variant_id)
    item, created = CartItem.objects.get_or_create(cart=cart, product_variant=variant)
    if not created:
        item.quantity += quantity
    item.save()
    return redirect('cart_detail')


@require_POST
def update_cart_item(request, item_id):
    cart = get_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    quantity = int(request.POST.get('quantity', 1))
    if quantity > 0:
        item.quantity = quantity
        item.save()
    else:
        item.delete()
    return redirect('cart_detail')


@require_POST
def remove_cart_item(request, item_id):
    cart = get_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.delete()
    return redirect('cart_detail')


@login_required
def wishlist_detail(request):
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    return render(request, 'wishlist/wishlist_detail.html', {'wishlist': wishlist})


@login_required
@require_POST
def add_to_wishlist(request):
    product_id = request.POST.get('product_id')
    product = get_object_or_404(Product, id=product_id)
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    WishlistItem.objects.get_or_create(wishlist=wishlist, product=product)
    return redirect('wishlist_detail')


@login_required
@require_POST
def remove_from_wishlist(request, item_id):
    wishlist = get_object_or_404(Wishlist, user=request.user)
    item = get_object_or_404(WishlistItem, id=item_id, wishlist=wishlist)
    item.delete()
    return redirect('wishlist_detail')


def vendor_detail(request, username):
    """Vendor products view"""
    vendor = get_object_or_404(MnoryUser, username=username, is_vendor=True, is_active=True)

    products = Product.objects.filter(
        vendor=vendor,
        is_active=True,
        is_available=True
    ).select_related('category', 'subcategory', 'brand')

    # Filters
    subcategory_filter = request.GET.get('subcategory')
    fit_type_filter = request.GET.get('fit_type')
    brand_filter = request.GET.get('brand')
    color_filter = request.GET.get('color')
    size_filter = request.GET.get('size')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort', 'name')

    if subcategory_filter:
        products = products.filter(subcategory__slug=subcategory_filter)

    if fit_type_filter:
        products = products.filter(fit_type__slug=fit_type_filter)

    if brand_filter:
        products = products.filter(brand__slug=brand_filter)

    if color_filter:
        products = products.filter(colors__name__icontains=color_filter)

    if size_filter:
        products = products.filter(sizes__name__icontains=size_filter)

    if min_price:
        products = products.filter(price__gte=min_price)

    if max_price:
        products = products.filter(price__lte=max_price)

    # Sorting
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'popular':
        products = products.order_by('-is_best_seller', '-created_at')
    else:
        products = products.order_by('name')

    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Filters
    fit_types = FitType.objects.filter(is_active=True)
    brands = Brand.objects.filter(is_active=True)
    colors = Color.objects.filter(is_active=True)
    sizes = Size.objects.filter(is_active=True)
    all_categories = Category.objects.filter(is_active=True)

    # Price range
    price_range = Product.objects.filter(
        vendor=vendor,
        is_active=True,
        is_available=True
    ).aggregate(Min('price'), Max('price'))

    context = {
        'vendor': vendor,
        'products': page_obj,
        'fit_types': fit_types,
        'brands': brands,
        'colors': colors,
        'sizes': sizes,
        'price_range': price_range,
        'categories': all_categories,
        'current_filters': {
            'subcategory': subcategory_filter,
            'fit_type': fit_type_filter,
            'brand': brand_filter,
            'color': color_filter,
            'size': size_filter,
            'min_price': min_price,
            'max_price': max_price,
            'sort': sort_by,
        }
    }

    return render(request, 'shop/vendor_detail.html', context)
