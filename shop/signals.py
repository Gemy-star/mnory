from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from .email import (
    send_order_confirmation_email,
    send_order_status_update_email,
    send_customer_welcome_email,
    send_vendor_registration_email,
    send_vendor_approval_email,
    send_vendor_rejection_email,
    send_admin_new_order_notification,
    send_admin_new_vendor_notification
)
from .models import Order, MnoryUser, VendorProfile
from shop.models import ProductVariant, Cart, CartItem, Wishlist, Product, WishlistItem, MnoryUser, VendorProfile
import logging

logger = logging.getLogger(__name__)

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


# -------------------------------
# Order Related Signals
# -------------------------------

@receiver(post_save, sender=Order)
def handle_order_created(sender, instance, created, **kwargs):
    """
    Send order confirmation email when a new order is created
    """
    if created:
        logger.info(f"New order created: {instance.order_number}")
        
        # Send order confirmation email to customer
        try:
            send_order_confirmation_email(instance)
        except Exception as e:
            logger.error(f"Failed to send order confirmation email for order {instance.order_number}: {str(e)}")
        
        # Send admin notification
        try:
            send_admin_new_order_notification(instance)
        except Exception as e:
            logger.error(f"Failed to send admin notification for order {instance.order_number}: {str(e)}")

@receiver(pre_save, sender=Order)
def handle_order_status_change(sender, instance, **kwargs):
    """
    Send order status update email when order status changes
    """
    if instance.pk:  # Only for existing orders
        try:
            old_instance = Order.objects.get(pk=instance.pk)
            old_status = old_instance.status
            new_status = instance.status
            
            # Check if status actually changed
            if old_status != new_status:
                logger.info(f"Order {instance.order_number} status changed from {old_status} to {new_status}")
                
                # Send status update email after the save completes
                from django.db import transaction
                transaction.on_commit(
                    lambda: send_order_status_update_email(instance, old_status, new_status)
                )
        except Order.DoesNotExist:
            # This shouldn't happen, but handle gracefully
            logger.warning(f"Could not find existing order {instance.pk} for status change comparison")
        except Exception as e:
            logger.error(f"Error handling order status change for {instance.order_number}: {str(e)}")

# -------------------------------
# User Registration Signals
# -------------------------------

@receiver(post_save, sender=MnoryUser)
def handle_user_registration(sender, instance, created, **kwargs):
    """
    Send welcome email when a new user registers
    """
    if created:
        logger.info(f"New user registered: {instance.email}")
        
        # Only send welcome email for customers, not vendors or admins
        if instance.user_type == 'customer':
            try:
                send_customer_welcome_email(instance)
            except Exception as e:
                logger.error(f"Failed to send welcome email to {instance.email}: {str(e)}")

# -------------------------------
# Vendor Related Signals
# -------------------------------

@receiver(post_save, sender=VendorProfile)
def handle_vendor_profile_created(sender, instance, created, **kwargs):
    """
    Send vendor registration email when a vendor profile is created
    """
    if created:
        logger.info(f"New vendor profile created: {instance.store_name}")
        
        try:
            # Send registration email to vendor
            send_vendor_registration_email(instance.user, instance)
            
            # Send admin notification
            send_admin_new_vendor_notification(instance.user, instance)
        except Exception as e:
            logger.error(f"Failed to send vendor registration emails for {instance.user.email}: {str(e)}")

@receiver(pre_save, sender=VendorProfile)
def handle_vendor_approval_change(sender, instance, **kwargs):
    """
    Send approval/rejection emails when vendor approval status changes
    """
    if instance.pk:  # Only for existing vendor profiles
        try:
            old_instance = VendorProfile.objects.get(pk=instance.pk)
            old_approval_status = old_instance.is_approved
            new_approval_status = instance.is_approved
            
            # Check if approval status changed
            if old_approval_status != new_approval_status:
                logger.info(f"Vendor {instance.store_name} approval status changed to {new_approval_status}")
                
                from django.db import transaction
                
                if new_approval_status:
                    # Vendor was approved
                    transaction.on_commit(
                        lambda: send_vendor_approval_email(instance.user, instance)
                    )
                else:
                    # Vendor was rejected (if they were previously approved)
                    if old_approval_status:
                        transaction.on_commit(
                            lambda: send_vendor_rejection_email(instance.user, instance, "Your vendor account has been suspended.")
                        )
                        
        except VendorProfile.DoesNotExist:
            logger.warning(f"Could not find existing vendor profile {instance.pk} for approval change comparison")
        except Exception as e:
            logger.error(f"Error handling vendor approval change for {instance.user.email}: {str(e)}")

# -------------------------------
# Optional: Login tracking for first-time users
# -------------------------------

@receiver(user_logged_in)
def handle_user_first_login(sender, request, user, **kwargs):
    """
    Optional: Track first login or send additional welcome emails
    """
    # You can implement additional logic here if needed
    # For example, tracking user login analytics or sending follow-up emails
    pass

# -------------------------------
# Utility Functions for Manual Email Sending
# -------------------------------

def send_manual_vendor_rejection_email(vendor_profile, reason=""):
    """
    Manually send vendor rejection email with custom reason
    """
    try:
        success = send_vendor_rejection_email(vendor_profile.user, vendor_profile, reason)
        if success:
            logger.info(f"Manual vendor rejection email sent to {vendor_profile.user.email}")
        else:
            logger.error(f"Failed to send manual vendor rejection email to {vendor_profile.user.email}")
        return success
    except Exception as e:
        logger.error(f"Error sending manual vendor rejection email: {str(e)}")
        return False

def send_bulk_promotional_email(user_queryset, subject, template_name, context):
    """
    Send promotional emails to multiple users
    Note: Be careful with bulk emails and respect email preferences
    """
    from .email import send_email_with_sendgrid
    
    success_count = 0
    failure_count = 0
    
    for user in user_queryset:
        try:
            # Add user-specific context
            user_context = context.copy()
            user_context.update({
                'user': user,
                'customer_name': user.get_full_name() or user.email.split('@')[0],
            })
            
            success = send_email_with_sendgrid(
                to_email=user.email,
                subject=subject,
                template_name=template_name,
                context=user_context
            )
            
            if success:
                success_count += 1
            else:
                failure_count += 1
                
        except Exception as e:
            logger.error(f"Error sending promotional email to {user.email}: {str(e)}")
            failure_count += 1
    
    logger.info(f"Bulk email completed: {success_count} sent, {failure_count} failed")
    return success_count, failure_count

# -------------------------------
# Test Functions
# -------------------------------

def test_order_confirmation_email(order_id):
    """
    Test order confirmation email for a specific order
    """
    try:
        order = Order.objects.get(id=order_id)
        success = send_order_confirmation_email(order)
        print(f"Order confirmation email test: {'✅ Success' if success else '❌ Failed'}")
        return success
    except Order.DoesNotExist:
        print(f"❌ Order with ID {order_id} not found")
        return False
    except Exception as e:
        print(f"❌ Error testing order confirmation email: {str(e)}")
        return False

def test_customer_welcome_email(user_id):
    """
    Test customer welcome email for a specific user
    """
    try:
        user = MnoryUser.objects.get(id=user_id)
        success = send_customer_welcome_email(user)
        print(f"Customer welcome email test: {'✅ Success' if success else '❌ Failed'}")
        return success
    except MnoryUser.DoesNotExist:
        print(f"❌ User with ID {user_id} not found")
        return False
    except Exception as e:
        print(f"❌ Error testing customer welcome email: {str(e)}")
        return False

def test_vendor_registration_email(vendor_profile_id):
    """
    Test vendor registration email for a specific vendor profile
    """
    try:
        vendor_profile = VendorProfile.objects.get(id=vendor_profile_id)
        success = send_vendor_registration_email(vendor_profile.user, vendor_profile)
        print(f"Vendor registration email test: {'✅ Success' if success else '❌ Failed'}")
        return success
    except VendorProfile.DoesNotExist:
        print(f"❌ Vendor profile with ID {vendor_profile_id} not found")
        return False
    except Exception as e:
        print(f"❌ Error testing vendor registration email: {str(e)}")
        return False