from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.db.models.signals import post_save

from shop.models import ProductVariant, Cart, CartItem, Wishlist, Product, WishlistItem, MnoryUser, VendorProfile


@receiver(post_save, sender=MnoryUser)
def create_vendor_profile(sender, instance, created, **kwargs):
    """
    Signal handler to create a VendorProfile automatically when a MnoryUser
    with user_type 'vendor' is created.
    """
    # Check if the user was just created and their user_type is 'vendor'
    # The 'is_vendor' attribute no longer exists on MnoryUser; use 'user_type' instead.
    if created and instance.user_type == 'vendor':
        # Ensure a VendorProfile doesn't already exist for this user
        # This check prevents errors if the signal is triggered multiple times
        # or if a profile was manually created.
        if not hasattr(instance, 'vendorprofile'):
            VendorProfile.objects.create(user=instance)
            # Optional: Add logging or print statement for debugging
            # print(f"VendorProfile created for new vendor user: {instance.email}")


@receiver(user_logged_in)
def merge_session_cart_wishlist(sender, user, request, **kwargs):
    """
    Signal handler to merge session-based cart and wishlist data into
    the user's permanent cart/wishlist upon successful login.
    """
    # --- Cart Merge Logic ---
    session_cart = request.session.get('cart', {})
    if session_cart:
        # Get or create the user's persistent cart
        cart, _ = Cart.objects.get_or_create(user=user)

        for variant_id, quantity in session_cart.items():
            # Ensure the variant exists
            variant = ProductVariant.objects.filter(id=variant_id).first()
            if variant:
                # Get or create the cart item
                item, created = CartItem.objects.get_or_create(cart=cart, product_variant=variant)
                if not created:
                    # If item already exists, add the quantity from session
                    item.quantity += quantity
                else:
                    # If new item, set its quantity
                    item.quantity = quantity
                item.save()
        # Clear the session cart after merging
        request.session.pop('cart', None)  # Use .pop(key, default) for safer removal

    # --- Wishlist Merge Logic ---
    session_wishlist = request.session.get('wishlist', [])
    if session_wishlist:
        # Get or create the user's persistent wishlist
        wishlist, _ = Wishlist.objects.get_or_create(user=user)

        for product_id in session_wishlist:
            # Ensure the product exists
            product = Product.objects.filter(id=product_id).first()
            if product:
                # Add product to wishlist if not already there
                WishlistItem.objects.get_or_create(wishlist=wishlist, product=product)
        # Clear the session wishlist after merging
        request.session.pop('wishlist', None)  # Use .pop(key, default) for safer removal

