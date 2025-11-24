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
        "api/add-to-wishlist/",
        views.add_to_wishlist,
        name="add_to_wishlist",
    ),  # Renamed, consolidated all add-to-wishlist here
    path(
        "api/get-counts/",
        views.get_cart_and_wishlist_counts,
        name="get_cart_and_wishlist_counts",
    ),  # GET for counts (new endpoint)
    # Legacy counts URL to support older JS paths like ajax/cart-count/
    path(
        "ajax/cart-count/",
        views.get_cart_and_wishlist_counts,
        name="cart_count_legacy",
    ),
    path(
        "api/get-shipping-cost/",
        views.get_shipping_cost,
        name="get_shipping_cost",
    ),  # GET for shipping cost based on city
    path(
        "api/get-available-sizes/<int:product_id>/",
        views.get_available_sizes_ajax,
        name="get_available_sizes_ajax",
    ),
    path("api/apply-coupon/", views.apply_coupon, name="apply_coupon"),
    path("api/remove-coupon/", views.remove_coupon, name="remove_coupon"),
    path("api/chatbot/", views.chatbot_api, name="chatbot_api"),
    # Advertisement tracking
    path("api/track-ad-view/", views.track_ad_view, name="track_ad_view"),
    path("api/track-ad-click/", views.track_ad_click, name="track_ad_click"),
    # Static Pages
    path(
        "terms/",
        TemplateView.as_view(template_name="shop/terms.html"),
        name="terms",
    ),
    path(
        "policy/",
        TemplateView.as_view(template_name="shop/policy.html"),
        name="policy",
    ),
    # Cart Views
    path("cart/", views.cart_view, name="cart_view"),
    path(
        "cart/update-quantity/",
        views.update_cart_quantity,
        name="update_cart_quantity",
    ),
    path("cart/remove/", views.remove_from_cart, name="remove_from_cart"),
    # Wishlist Views
    path("wishlist/", views.wishlist_view, name="wishlist_view"),
    path(
        "wishlist/remove/",
        views.remove_from_wishlist,
        name="remove_from_wishlist",
    ),  # Specific endpoint for removal
    # Checkout & Order Views
    path("checkout/", views.checkout_view, name="checkout"),
    path("checkout/process/", views.process_order, name="process_order"),
    path(
        "order/confirmation/<str:order_number>/",
        views.order_confirmation,
        name="order_confirmation",
    ),
    # path(
    #     "order/anonymous_confirmation/<int:order_id>/<uuid:token>/",
    #     views.order_confirmation_anonymous_view,
    #     name="order_confirmation_anonymous",
    # ),
    path("orders/", views.order_history, name="order_history"),
    path("orders/<str:order_number>/", views.order_detail, name="order_detail"),
    # Buy Now
    path("buy-now/", extra_views.buy_now_view, name="buy_now"),
    # Accounts Views
    path("register/vendor/", user_views.register_vendor, name="register_vendor"),
    path(
        "register/customer/",
        user_views.register_customer,
        name="register_customer",
    ),
    path("logout/", user_views.user_logout, name="logout"),
    path("login/", user_views.login_view, name="login"),
    path("account/profile/", views.profile_view, name="profile"),
    path("account/profile/edit/", views.edit_profile, name="edit_profile"),
    path("account/addresses/", views.address_list, name="address_list"),
    path("account/addresses/add/", views.address_add, name="address_add"),
    path(
        "account/addresses/edit/<int:address_id>/",
        views.address_edit,
        name="address_edit",
    ),
    path(
        "account/addresses/delete/<int:address_id>/",
        views.address_delete,
        name="address_delete",
    ),
    path("account/settings/", views.account_settings, name="account_settings"),
    # Admin Dashboard
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    # Admin Management Pages
    path("admin-products/", views.admin_products, name="admin_products"),
    path("admin-products/add/", views.admin_product_add, name="admin_product_add"),
    path(
        "admin-products/<int:product_id>/edit/",
        views.admin_product_edit,
        name="admin_product_edit",
    ),
    path(
        "admin-products/<int:product_id>/toggle-status/",
        views.admin_product_toggle_status,
        name="admin_product_toggle_status",
    ),
    path(
        "admin-products/<int:product_id>/delete/",
        views.admin_product_delete,
        name="admin_product_delete",
    ),
    path("admin-orders/", views.admin_orders, name="admin_orders"),
    path(
        "admin-orders/<int:order_id>/update-status/",
        views.admin_order_update_status,
        name="admin_order_update_status",
    ),
    path("admin-payments/", views.admin_payments, name="admin_payments"),
    path("admin-users/", views.admin_users, name="admin_users"),
    path(
        "admin-users/<int:user_id>/toggle-status/",
        views.admin_user_toggle_status,
        name="admin_user_toggle_status",
    ),
    path(
        "admin-users/<int:user_id>/delete/",
        views.admin_user_delete,
        name="admin_user_delete",
    ),
    path("admin-vendors/", views.admin_vendors, name="admin_vendors"),
    path(
        "admin-vendors/<int:vendor_id>/toggle-status/",
        views.admin_vendor_toggle_status,
        name="admin_vendor_toggle_status",
    ),
    path("admin-ads/", views.admin_ads, name="admin_ads"),
    path("admin-ads/add/", views.admin_ad_add, name="admin_ad_add"),
    path("admin-ads/<int:ad_id>/edit/", views.admin_ad_edit, name="admin_ad_edit"),
    path(
        "admin-ads/<int:ad_id>/toggle-status/",
        views.admin_ad_toggle_status,
        name="admin_ad_toggle_status",
    ),
    path(
        "admin-ads/<int:ad_id>/delete/", views.admin_ad_delete, name="admin_ad_delete"
    ),
    path("admin-coupons/", views.admin_coupons, name="admin_coupons"),
    path("admin-coupons/add/", views.admin_coupon_add, name="admin_coupon_add"),
    path(
        "admin-coupons/<int:coupon_id>/edit/",
        views.admin_coupon_edit,
        name="admin_coupon_edit",
    ),
    path(
        "admin-coupons/<int:coupon_id>/toggle-status/",
        views.admin_coupon_toggle_status,
        name="admin_coupon_toggle_status",
    ),
    path(
        "admin-coupons/<int:coupon_id>/delete/",
        views.admin_coupon_delete,
        name="admin_coupon_delete",
    ),
    path("admin-settings/", views.admin_site_settings, name="admin_site_settings"),
    path("admin-chatbot/", views.admin_chatbot, name="admin_chatbot"),
    path(
        "admin-chatbot/create/", views.admin_chatbot_create, name="admin_chatbot_create"
    ),
    path(
        "admin-chatbot/<int:qa_id>/get/",
        views.admin_chatbot_get,
        name="admin_chatbot_get",
    ),
    path(
        "admin-chatbot/<int:qa_id>/update/",
        views.admin_chatbot_update,
        name="admin_chatbot_update",
    ),
    path(
        "admin-chatbot/<int:qa_id>/delete/",
        views.admin_chatbot_delete,
        name="admin_chatbot_delete",
    ),
    # Vendor Dashboard & Management
    path("vendor/dashboard/", views.vendor_dashboard, name="vendor_dashboard"),
    path(
        "vendor/products/",
        views.vendor_manage_products,
        name="vendor_manage_products",
    ),
    path(
        "vendor/products/add/",
        views.vendor_add_product,
        name="vendor_add_product",
    ),
    path(
        "vendor/products/bulk-stock-edit/",
        views.vendor_bulk_stock_edit,
        name="vendor_bulk_stock_edit",
    ),
    path(
        "vendor/orders/",
        views.vendor_manage_orders,
        name="vendor_manage_orders",
    ),
    path(
        "vendor/export/sales/",
        views.vendor_export_sales_csv,
        name="vendor_export_sales_csv",
    ),
    path(
        "vendor/shipping/",
        views.vendor_manage_shipping,
        name="vendor_manage_shipping",
    ),
    path(
        "vendor/payouts/request/",
        views.vendor_request_payout,
        name="vendor_request_payout",
    ),
    path(
        "vendor/products/edit/<int:product_id>/",
        views.vendor_edit_product,
        name="vendor_edit_product",
    ),
    path(
        "vendor/review/reply/<int:review_id>/",
        views.vendor_reply_to_review,
        name="vendor_reply_to_review",
    ),
    path(
        "vendor/products/delete/<int:product_id>/",
        views.vendor_delete_product,
        name="vendor_delete_product",
    ),
    path(
        "vendor/reviews/",
        views.vendor_manage_reviews,
        name="vendor_manage_reviews",
    ),
    path(
        "vendor/notifications/mark-as-read/",
        views.vendor_mark_notifications_as_read,
        name="vendor_mark_notifications_as_read",
    ),
    # Global notifications for any logged-in user
    path(
        "notifications/",
        views.notifications_list,
        name="notifications_list",
    ),
    path(
        "notifications/mark-as-read/",
        views.mark_notifications_as_read,
        name="mark_notifications_as_read",
    ),
    path(
        "product/<int:product_id>/review/",
        views.submit_review,
        name="submit_review",
    ),
    # change Currency
    path("set-currency/", extra_views.set_currency, name="set_currency"),
]
