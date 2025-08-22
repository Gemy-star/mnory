"""
Simple Email service functions for vendor management using SendGrid
File: main/email_utils.py
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