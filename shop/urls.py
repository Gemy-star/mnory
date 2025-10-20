from django.urls import path
from . import views, extra_views, user_views
from django.views.generic import TemplateView

app_name = "shop"

urlpatterns = [
    # Core Product & Category Views
    path("", views.home, name="home"),
    path("category/<slug:slug>/", views.category_detail, name="category_detail"),
    path(
        "category/<slug:category_slug>/<slug:slug>/",
        views.subcategory_detail,
        name="subcategory_detail",
    ),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),
    path("vendor/<slug:slug>/", views.vendor_detail, name="vendor_detail"),
    # Search & API Endpoints (All AJAX actions should typically be POST)
    path(
        "search/", views.search_products, name="search_products"
    ),  # GET for search results
    path(
        "api/products/",
        views.get_category_products_api,
        name="get_category_products_api",
    ),  # GET for category products
    path(
        "api/variants/<int:product_id>/",
        views.get_product_variants,
        name="get_product_variants",
    ),  # GET for variant data
    path(
        "api/add-to-cart/", views.add_to_cart, name="add_to_cart"
    ),  # Renamed, consolidated all add-to-cart here
    path(
        "api/add-to-wishlist/", views.add_to_wishlist, name="add_to_wishlist"
    ),  # Renamed, consolidated all add-to-wishlist here
    path(
        "api/get-counts/",
        views.get_cart_and_wishlist_counts,
        name="get_cart_and_wishlist_counts",
    ),  # GET for counts
    path(
        "api/get-available-sizes/<int:product_id>/",
        views.get_available_sizes_ajax,
        name="get_available_sizes_ajax",
    ),
    # path('api/apply-coupon/', views.apply_coupon, name='apply_coupon'),
    # Advertisement tracking
    path("api/track-ad-view/", views.track_ad_view, name="track_ad_view"),
    path("api/track-ad-click/", views.track_ad_click, name="track_ad_click"),
    # Static Pages
    path("terms/", TemplateView.as_view(template_name="shop/terms.html"), name="terms"),
    path(
        "policy/", TemplateView.as_view(template_name="shop/policy.html"), name="policy"
    ),
    # Cart Views
    path("cart/", views.cart_view, name="cart_view"),
    path(
        "cart/update-quantity/", views.update_cart_quantity, name="update_cart_quantity"
    ),
    path("cart/remove/", views.remove_from_cart, name="remove_from_cart"),
    # Wishlist Views
    path("wishlist/", views.wishlist_view, name="wishlist_view"),
    path(
        "wishlist/remove/", views.remove_from_wishlist, name="remove_from_wishlist"
    ),  # Specific endpoint for removal
    # Checkout & Order Views
    path("checkout/", views.checkout_view, name="checkout"),
    path("checkout/process/", views.process_order, name="process_order"),
    path(
        "order/confirmation/<str:order_number>/",
        views.order_confirmation,
        name="order_confirmation",
    ),
    # path('order/anonymous_confirmation/<int:order_id>/<uuid:token>/', views.order_confirmation_anonymous_view,
    #      name='order_confirmation_anonymous'),
    path("orders/", views.order_history, name="order_history"),
    path("orders/<str:order_number>/", views.order_detail, name="order_detail"),
    # Buy Now
    path("buy-now/", extra_views.buy_now_view, name="buy_now"),
    # Accounts Views
    path("register/vendor/", user_views.register_vendor, name="register_vendor"),
    path("register/customer/", user_views.register_customer, name="register_customer"),
    path("logout/", user_views.user_logout, name="logout"),
    path("login/", user_views.login_view, name="login"),
    # change Currency
    path("set-currency/", extra_views.set_currency, name="set_currency"),
]
