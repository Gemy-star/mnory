from django.urls import path
from . import views
from django.views.generic import TemplateView
from . import  cart_wish_views
app_name = 'shop'

urlpatterns = [
    path('', views.home, name='home'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('category/<slug:category_slug>/<slug:slug>/', views.subcategory_detail, name='subcategory_detail'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('search/', views.search_products, name='search_products'),
    path('api/variants/<int:product_id>/', views.get_product_variants, name='get_product_variants'),
    path('api/add-to-cart/', views.add_to_cart, name='add_to_cart'), # New AJAX endpoint for cart
    path('api/add-to-wishlist/', views.add_to_wishlist, name='add_to_wishlist'), # New AJAX endpoint for wishlist
    path('api/get-counts/', views.get_cart_and_wishlist_counts, name='get_cart_and_wishlist_counts'), # New AJAX endpoint for counts
    path('account/', views.account_view, name='account'),
    path('vendor/<slug:slug>/', views.vendor_detail, name='vendor_detail'),
    path('terms/', TemplateView.as_view(template_name="shop/terms.html"), name="terms"),
    path('policy/', TemplateView.as_view(template_name="shop/policy.html"), name="policy"),
    path('cart/', cart_wish_views.cart_view, name='cart_view'),
    path('wishlist/', cart_wish_views.wishlist_view, name='wishlist_view'),
    path('wishlist/add/<int:product_id>/', cart_wish_views.add_to_wishlist, name='add_to_wishlist'),
    path('cart/add/<int:variant_id>/', cart_wish_views.add_to_cart, name='add_to_cart'),
    path("cart/remove/<int:variant_id>/", cart_wish_views.remove_from_cart, name="remove_from_cart"),
]