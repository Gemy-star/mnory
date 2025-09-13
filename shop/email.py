"""
Enhanced Email service functions for vendor management using SendGrid
File: main/utils.py
"""
import logging
import os
from django.template import loader, TemplateDoesNotExist
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from constance import config

logger = logging.getLogger(__name__)

# -------------------------------
# Basic SendGrid Email Function
# -------------------------------

def send_email_with_sendgrid(to_email, subject, template_name, context):
    """
    Send an email using the SendGrid API with HTML and text versions.
    """
    logger.info(f"SendGrid: Starting email send process to {to_email} with template '{template_name}'")

    try:
        # Check SendGrid API key
        api_key = config.SENDGRID_API_KEY
        if not api_key:
            logger.error("SendGrid: No API key found in config or environment variables")
            return False

        # Check from email
        from_email = getattr(config, 'ADMIN_EMAIL', None)
        if not from_email:
            logger.error("SendGrid: No ADMIN_EMAIL found in config")
            return False

        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, to_email):
            logger.error(f"SendGrid: Invalid email format: {to_email}")
            return False

        # Load HTML template
        try:
            html_template_path = f"email/{template_name}.html"
            html_content = loader.render_to_string(html_template_path, context)
            logger.info(f"SendGrid: HTML template loaded successfully, length: {len(html_content)} chars")
        except TemplateDoesNotExist:
            logger.error(f"SendGrid: HTML template not found: {html_template_path}")
            return False
        except Exception as e:
            logger.error(f"SendGrid: Failed to load HTML template '{html_template_path}': {str(e)}")
            return False

        # Load text template (optional)
        try:
            text_template_path = f"email/{template_name}.txt"
            text_content = loader.render_to_string(text_template_path, context)
            logger.info(f"SendGrid: Text template loaded successfully")
        except TemplateDoesNotExist:
            text_content = f"{subject}\n\nPlease enable HTML to view this email."
            logger.info(f"SendGrid: Text template not found, using fallback content")
        except Exception as e:
            logger.warning(f"SendGrid: Error loading text template, using fallback: {str(e)}")
            text_content = f"{subject}\n\nPlease enable HTML to view this email."

        # Create SendGrid Mail object
        try:
            message = Mail(
                from_email=from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content,
                plain_text_content=text_content
            )
            logger.info("SendGrid: Mail object created successfully")
        except Exception as e:
            logger.error(f"SendGrid: Failed to create Mail object: {str(e)}")
            return False

        # Initialize SendGrid client and send
        try:
            sg = SendGridAPIClient(api_key=api_key)

            # Uncomment if using EU region
            # sg.set_sendgrid_data_residency("eu")

            response = sg.send(message)

            logger.info(f"SendGrid: API call completed - Status: {response.status_code}")

            if response.status_code in [200, 201, 202]:
                logger.info(f"SendGrid: Email sent successfully to {to_email} with template '{template_name}'")
                return True
            else:
                logger.error(f"SendGrid: Unexpected status code {response.status_code}")
                if hasattr(response, 'body') and response.body:
                    logger.error(f"SendGrid: Response body: {response.body}")
                return False

        except Exception as e:
            # This will catch all SendGrid API errors
            logger.error(f"SendGrid: API call failed: {str(e)}")
            logger.error(f"SendGrid: Exception type: {type(e).__name__}")

            # Try to extract more details from the exception
            if hasattr(e, 'status_code'):
                logger.error(f"SendGrid: Status code: {e.status_code}")
            if hasattr(e, 'body'):
                logger.error(f"SendGrid: Error body: {e.body}")
            elif hasattr(e, 'message'):
                logger.error(f"SendGrid: Error message: {e.message}")

            return False

    except Exception as e:
        logger.exception(f"SendGrid: Unexpected error in send_email_with_sendgrid for {to_email}: {str(e)}")
        return False

# -------------------------------
# Order Confirmation Email
# -------------------------------

def send_order_confirmation_email(order):
    """
    Send order confirmation email to customer
    """
    logger.info(f"Sending order confirmation email for order: {order.order_number}")
    
    try:
        # Prepare context for email template
        context = {
            'order': order,
            'customer_name': order.full_name,
            'order_number': order.order_number,
            'order_items': order.items.all(),
            'subtotal': order.subtotal,
            'shipping_cost': order.shipping_cost,
            'grand_total': order.grand_total,
            'shipping_address': getattr(order, 'shipping_address', None),
            'order_date': order.created_at,
            'site_name': getattr(config, 'SITE_NAME', 'Mnory Store'),
            'support_email': getattr(config, 'ADMIN_EMAIL', 'support@mnory.com'),
        }
        
        subject = f"Order Confirmation - {order.order_number}"
        
        # Send email to customer
        success = send_email_with_sendgrid(
            to_email=order.email,
            subject=subject,
            template_name='order_confirmation',
            context=context
        )
        
        if success:
            logger.info(f"Order confirmation email sent successfully for order: {order.order_number}")
        else:
            logger.error(f"Failed to send order confirmation email for order: {order.order_number}")
            
        return success
        
    except Exception as e:
        logger.exception(f"Error sending order confirmation email for order {order.order_number}: {str(e)}")
        return False

def send_order_status_update_email(order, old_status, new_status):
    """
    Send order status update email to customer
    """
    logger.info(f"Sending order status update email for order: {order.order_number}")
    
    try:
        context = {
            'order': order,
            'customer_name': order.full_name,
            'order_number': order.order_number,
            'old_status': old_status,
            'new_status': new_status,
            'status_display': order.get_status_display(),
            'order_url': f"{getattr(config, 'SITE_URL', '')}/orders/{order.order_number}/",
            'site_name': getattr(config, 'SITE_NAME', 'Mnory Store'),
            'support_email': getattr(config, 'ADMIN_EMAIL', 'support@mnory.com'),
        }
        
        subject = f"Order Update - {order.order_number} is now {order.get_status_display()}"
        
        success = send_email_with_sendgrid(
            to_email=order.email,
            subject=subject,
            template_name='order_status_update',
            context=context
        )
        
        if success:
            logger.info(f"Order status update email sent successfully for order: {order.order_number}")
        else:
            logger.error(f"Failed to send order status update email for order: {order.order_number}")
            
        return success
        
    except Exception as e:
        logger.exception(f"Error sending order status update email for order {order.order_number}: {str(e)}")
        return False

# -------------------------------
# Customer Registration Emails
# -------------------------------

def send_customer_welcome_email(user):
    """
    Send welcome email to newly registered customer
    """
    logger.info(f"Sending welcome email to customer: {user.email}")
    
    try:
        context = {
            'user': user,
            'customer_name': user.get_full_name() or user.email.split('@')[0],
            'email': user.email,
            'login_url': f"{getattr(config, 'SITE_URL', '')}/login/",
            'shop_url': f"{getattr(config, 'SITE_URL', '')}/shop/",
            'site_name': getattr(config, 'SITE_NAME', 'Mnory Store'),
            'support_email': getattr(config, 'ADMIN_EMAIL', 'support@mnory.com'),
        }
        
        subject = f"Welcome to {getattr(config, 'SITE_NAME', 'Mnory Store')}!"
        
        success = send_email_with_sendgrid(
            to_email=user.email,
            subject=subject,
            template_name='customer_welcome',
            context=context
        )
        
        if success:
            logger.info(f"Welcome email sent successfully to customer: {user.email}")
        else:
            logger.error(f"Failed to send welcome email to customer: {user.email}")
            
        return success
        
    except Exception as e:
        logger.exception(f"Error sending welcome email to customer {user.email}: {str(e)}")
        return False

# -------------------------------
# Vendor Registration Emails
# -------------------------------

def send_vendor_registration_email(user, vendor_profile):
    """
    Send registration confirmation email to newly registered vendor
    """
    logger.info(f"Sending registration email to vendor: {user.email}")
    
    try:
        context = {
            'user': user,
            'vendor_profile': vendor_profile,
            'vendor_name': user.get_full_name() or user.email.split('@')[0],
            'store_name': vendor_profile.store_name,
            'email': user.email,
            'dashboard_url': f"{getattr(config, 'SITE_URL', '')}/vendor/dashboard/",
            'approval_required': not vendor_profile.is_approved,
            'site_name': getattr(config, 'SITE_NAME', 'Mnory Store'),
            'support_email': getattr(config, 'ADMIN_EMAIL', 'support@mnory.com'),
        }
        
        subject = f"Welcome to {getattr(config, 'SITE_NAME', 'Mnory Store')} - Vendor Registration"
        
        success = send_email_with_sendgrid(
            to_email=user.email,
            subject=subject,
            template_name='vendor_registration',
            context=context
        )
        
        if success:
            logger.info(f"Vendor registration email sent successfully to: {user.email}")
        else:
            logger.error(f"Failed to send vendor registration email to: {user.email}")
            
        return success
        
    except Exception as e:
        logger.exception(f"Error sending vendor registration email to {user.email}: {str(e)}")
        return False

def send_vendor_approval_email(user, vendor_profile):
    """
    Send approval confirmation email to vendor
    """
    logger.info(f"Sending approval email to vendor: {user.email}")
    
    try:
        context = {
            'user': user,
            'vendor_profile': vendor_profile,
            'vendor_name': user.get_full_name() or user.email.split('@')[0],
            'store_name': vendor_profile.store_name,
            'email': user.email,
            'dashboard_url': f"{getattr(config, 'SITE_URL', '')}/vendor/dashboard/",
            'add_product_url': f"{getattr(config, 'SITE_URL', '')}/vendor/products/add/",
            'site_name': getattr(config, 'SITE_NAME', 'Mnory Store'),
            'support_email': getattr(config, 'ADMIN_EMAIL', 'support@mnory.com'),
        }
        
        subject = f"Congratulations! Your vendor account has been approved"
        
        success = send_email_with_sendgrid(
            to_email=user.email,
            subject=subject,
            template_name='vendor_approval',
            context=context
        )
        
        if success:
            logger.info(f"Vendor approval email sent successfully to: {user.email}")
        else:
            logger.error(f"Failed to send vendor approval email to: {user.email}")
            
        return success
        
    except Exception as e:
        logger.exception(f"Error sending vendor approval email to {user.email}: {str(e)}")
        return False

def send_vendor_rejection_email(user, vendor_profile, reason=""):
    """
    Send rejection email to vendor
    """
    logger.info(f"Sending rejection email to vendor: {user.email}")
    
    try:
        context = {
            'user': user,
            'vendor_profile': vendor_profile,
            'vendor_name': user.get_full_name() or user.email.split('@')[0],
            'store_name': vendor_profile.store_name,
            'email': user.email,
            'reason': reason,
            'reapply_url': f"{getattr(config, 'SITE_URL', '')}/vendor/register/",
            'site_name': getattr(config, 'SITE_NAME', 'Mnory Store'),
            'support_email': getattr(config, 'ADMIN_EMAIL', 'support@mnory.com'),
        }
        
        subject = f"Update on your vendor application"
        
        success = send_email_with_sendgrid(
            to_email=user.email,
            subject=subject,
            template_name='vendor_rejection',
            context=context
        )
        
        if success:
            logger.info(f"Vendor rejection email sent successfully to: {user.email}")
        else:
            logger.error(f"Failed to send vendor rejection email to: {user.email}")
            
        return success
        
    except Exception as e:
        logger.exception(f"Error sending vendor rejection email to {user.email}: {str(e)}")
        return False

# -------------------------------
# Admin Notification Emails
# -------------------------------

def send_admin_new_order_notification(order):
    """
    Send new order notification to admin
    """
    logger.info(f"Sending new order notification to admin for order: {order.order_number}")
    
    try:
        admin_email = getattr(config, 'ADMIN_EMAIL', None)
        if not admin_email:
            logger.error("No admin email configured")
            return False
            
        context = {
            'order': order,
            'order_number': order.order_number,
            'customer_name': order.full_name,
            'customer_email': order.email,
            'order_items': order.items.all(),
            'grand_total': order.grand_total,
            'order_date': order.created_at,
            'admin_url': f"{getattr(config, 'SITE_URL', '')}/admin/shop/order/{order.id}/",
            'site_name': getattr(config, 'SITE_NAME', 'Mnory Store'),
        }
        
        subject = f"New Order Received - {order.order_number}"
        
        success = send_email_with_sendgrid(
            to_email=admin_email,
            subject=subject,
            template_name='admin_new_order',
            context=context
        )
        
        if success:
            logger.info(f"Admin new order notification sent successfully for order: {order.order_number}")
        else:
            logger.error(f"Failed to send admin new order notification for order: {order.order_number}")
            
        return success
        
    except Exception as e:
        logger.exception(f"Error sending admin new order notification for order {order.order_number}: {str(e)}")
        return False

def send_admin_new_vendor_notification(user, vendor_profile):
    """
    Send new vendor registration notification to admin
    """
    logger.info(f"Sending new vendor notification to admin for vendor: {user.email}")
    
    try:
        admin_email = getattr(config, 'ADMIN_EMAIL', None)
        if not admin_email:
            logger.error("No admin email configured")
            return False
            
        context = {
            'user': user,
            'vendor_profile': vendor_profile,
            'vendor_name': user.get_full_name() or user.email.split('@')[0],
            'vendor_email': user.email,
            'store_name': vendor_profile.store_name,
            'registration_date': vendor_profile.user.date_joined,
            'admin_url': f"{getattr(config, 'SITE_URL', '')}/admin/shop/vendorprofile/{vendor_profile.id}/",
            'site_name': getattr(config, 'SITE_NAME', 'Mnory Store'),
        }
        
        subject = f"New Vendor Registration - {vendor_profile.store_name}"
        
        success = send_email_with_sendgrid(
            to_email=admin_email,
            subject=subject,
            template_name='admin_new_vendor',
            context=context
        )
        
        if success:
            logger.info(f"Admin new vendor notification sent successfully for vendor: {user.email}")
        else:
            logger.error(f"Failed to send admin new vendor notification for vendor: {user.email}")
            
        return success
        
    except Exception as e:
        logger.exception(f"Error sending admin new vendor notification for vendor {user.email}: {str(e)}")
        return False

# -------------------------------
# Test function
# -------------------------------

def test_sendgrid_setup():
    """
    Test SendGrid configuration and connection
    """
    api_key = getattr(config, 'SENDGRID_API_KEY', os.environ.get('SENDGRID_API_KEY'))
    from_email = getattr(config, 'ADMIN_EMAIL', None)

    print(f"API Key found: {'Yes' if api_key else 'No'}")
    if api_key:
        print(f"API Key starts with: {api_key[:10]}...")

    print(f"From email: {from_email}")

    if api_key and from_email:
        print("✅ Basic SendGrid setup looks correct")
        return True
    else:
        print("❌ SendGrid setup incomplete")
        return False

def test_email_sending():
    """
    Test email sending functionality with a simple test email
    """
    try:
        admin_email = getattr(config, 'ADMIN_EMAIL', None)
        if not admin_email:
            print("❌ No admin email configured for testing")
            return False
            
        context = {
            'test_message': 'This is a test email from the Mnory email system.',
            'timestamp': logger.info,
            'site_name': getattr(config, 'SITE_NAME', 'Mnory Store'),
        }
        
        success = send_email_with_sendgrid(
            to_email=admin_email,
            subject="Test Email - Mnory Email System",
            template_name='test_email',
            context=context
        )
        
        if success:
            print("✅ Test email sent successfully")
        else:
            print("❌ Test email failed to send")
            
        return success
        
    except Exception as e:
        print(f"❌ Error testing email sending: {str(e)}")
        return False