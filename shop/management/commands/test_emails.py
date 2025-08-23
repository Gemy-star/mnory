"""
Django management command for testing email functionality
File: management/commands/test_emails.py

Usage examples:
python manage.py test_emails --setup
python manage.py test_emails --test-basic
python manage.py test_emails --test-order 123
python manage.py test_emails --test-welcome 456
python manage.py test_emails --test-vendor 789
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from constance import config
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test email functionality for the Mnory store'

    def add_arguments(self, parser):
        parser.add_argument(
            '--setup',
            action='store_true',
            help='Test SendGrid setup and configuration',
        )
        parser.add_argument(
            '--test-basic',
            action='store_true',
            help='Send a basic test email',
        )
        parser.add_argument(
            '--test-order',
            type=int,
            help='Test order confirmation email for specific order ID',
        )
        parser.add_argument(
            '--test-welcome',
            type=int,
            help='Test customer welcome email for specific user ID',
        )
        parser.add_argument(
            '--test-vendor',
            type=int,
            help='Test vendor registration email for specific vendor profile ID',
        )
        parser.add_argument(
            '--test-all',
            action='store_true',
            help='Run all available email tests',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Override recipient email address for tests',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🧪 Email Testing Utility'))
        self.stdout.write('=' * 50)

        # Test setup
        if options['setup']:
            self.test_setup()

        # Test basic email sending
        if options['test_basic']:
            self.test_basic_email(options.get('email'))

        # Test order confirmation
        if options['test_order']:
            self.test_order_email(options['test_order'])

        # Test welcome email
        if options['test_welcome']:
            self.test_welcome_email(options['test_welcome'])

        # Test vendor email
        if options['test_vendor']:
            self.test_vendor_email(options['test_vendor'])

        # Run all tests
        if options['test_all']:
            self.run_all_tests()

        if not any([options['setup'], options['test_basic'], options['test_order'], 
                   options['test_welcome'], options['test_vendor'], options['test_all']]):
            self.stdout.write(self.style.WARNING('No test specified. Use --help for options.'))

    def test_setup(self):
        """Test SendGrid configuration"""
        self.stdout.write('\n📋 Testing SendGrid Configuration...')
        
        from shop.email import test_sendgrid_setup
        
        success = test_sendgrid_setup()
        
        if success:
            self.stdout.write(self.style.SUCCESS('✅ SendGrid configuration looks good!'))
        else:
            self.stdout.write(self.style.ERROR('❌ SendGrid configuration incomplete'))
            self.stdout.write('Please check your SENDGRID_API_KEY and ADMIN_EMAIL settings')

    def test_basic_email(self, recipient_email=None):
        """Send a basic test email"""
        self.stdout.write('\n📧 Testing Basic Email Sending...')
        
        try:
            from shop.email import test_email_sending
            
            if recipient_email:
                # Override admin email temporarily
                original_admin_email = getattr(config, 'ADMIN_EMAIL', None)
                config.ADMIN_EMAIL = recipient_email
                
            success = test_email_sending()
            
            if recipient_email:
                # Restore original admin email
                config.ADMIN_EMAIL = original_admin_email
            
            if success:
                self.stdout.write(self.style.SUCCESS('✅ Basic email test successful!'))
            else:
                self.stdout.write(self.style.ERROR('❌ Basic email test failed'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error testing basic email: {str(e)}'))

    def test_order_email(self, order_id):
        """Test order confirmation email"""
        self.stdout.write(f'\n📦 Testing Order Confirmation Email for Order ID: {order_id}')
        
        try:
            from shop.signals import test_order_confirmation_email
            
            success = test_order_confirmation_email(order_id)
            
            if success:
                self.stdout.write(self.style.SUCCESS('✅ Order confirmation email test successful!'))
            else:
                self.stdout.write(self.style.ERROR('❌ Order confirmation email test failed'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error testing order email: {str(e)}'))

    def test_welcome_email(self, user_id):
        """Test customer welcome email"""
        self.stdout.write(f'\n👋 Testing Customer Welcome Email for User ID: {user_id}')
        
        try:
            from shop.signals import test_customer_welcome_email
            
            success = test_customer_welcome_email(user_id)
            
            if success:
                self.stdout.write(self.style.SUCCESS('✅ Customer welcome email test successful!'))
            else:
                self.stdout.write(self.style.ERROR('❌ Customer welcome email test failed'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error testing welcome email: {str(e)}'))

    def test_vendor_email(self, vendor_profile_id):
        """Test vendor registration email"""
        self.stdout.write(f'\n🏪 Testing Vendor Registration Email for Vendor Profile ID: {vendor_profile_id}')
        
        try:
            from shop.signals import test_vendor_registration_email
            
            success = test_vendor_registration_email(vendor_profile_id)
            
            if success:
                self.stdout.write(self.style.SUCCESS('✅ Vendor registration email test successful!'))
            else:
                self.stdout.write(self.style.ERROR('❌ Vendor registration email test failed'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error testing vendor email: {str(e)}'))

    def run_all_tests(self):
        """Run all available email tests"""
        self.stdout.write('\n🧪 Running All Email Tests...')
        
        # Test setup first
        self.test_setup()
        
        # Test basic email
        self.test_basic_email()
        
        # Test with sample data if available
        try:
            from shop.models import Order, MnoryUser, VendorProfile
            
            # Test order email with latest order
            latest_order = Order.objects.first()
            if latest_order:
                self.test_order_email(latest_order.id)
            else:
                self.stdout.write(self.style.WARNING('⚠️  No orders found for testing'))
            
            # Test welcome email with latest customer
            latest_customer = MnoryUser.objects.filter(user_type='customer').first()
            if latest_customer:
                self.test_welcome_email(latest_customer.id)
            else:
                self.stdout.write(self.style.WARNING('⚠️  No customers found for testing'))
            
            # Test vendor email with latest vendor
            latest_vendor = VendorProfile.objects.first()
            if latest_vendor:
                self.test_vendor_email(latest_vendor.id)
            else:
                self.stdout.write(self.style.WARNING('⚠️  No vendor profiles found for testing'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error running comprehensive tests: {str(e)}'))
        
        self.stdout.write('\n🏁 All tests completed!')

    def create_test_data(self):
        """Create sample test data for email testing"""
        self.stdout.write('\n🔧 Creating Test Data...')
        
        try:
            from shop.models import MnoryUser, VendorProfile, Order, Category, Product, ProductVariant, Color, Size
            from decimal import Decimal
            
            # Create test customer
            test_customer, created = MnoryUser.objects.get_or_create(
                email='test.customer@example.com',
                defaults={
                    'username': 'test_customer',
                    'user_type': 'customer',
                    'first_name': 'Test',
                    'last_name': 'Customer'
                }
            )
            
            if created:
                self.stdout.write('✅ Test customer created')
            
            # Create test vendor user
            test_vendor_user, created = MnoryUser.objects.get_or_create(
                email='test.vendor@example.com',
                defaults={
                    'username': 'test_vendor',
                    'user_type': 'vendor',
                    'first_name': 'Test',
                    'last_name': 'Vendor'
                }
            )
            
            if created:
                self.stdout.write('✅ Test vendor user created')
            
            # Create test vendor profile
            test_vendor_profile, created = VendorProfile.objects.get_or_create(
                user=test_vendor_user,
                defaults={
                    'store_name': 'Test Store',
                    'store_description': 'A test store for email testing',
                    'is_approved': False
                }
            )
            
            if created:
                self.stdout.write('✅ Test vendor profile created')
            
            self.stdout.write(self.style.SUCCESS('✅ Test data creation completed!'))
            self.stdout.write(f'Customer ID: {test_customer.id}')
            self.stdout.write(f'Vendor Profile ID: {test_vendor_profile.id}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error creating test data: {str(e)}'))

    def cleanup_test_data(self):
        """Clean up test data"""
        self.stdout.write('\n🧹 Cleaning up test data...')
        
        try:
            from shop.models import MnoryUser, VendorProfile
            
            # Delete test users
            test_emails = ['test.customer@example.com', 'test.vendor@example.com']
            deleted_users = MnoryUser.objects.filter(email__in=test_emails).delete()
            
            self.stdout.write(self.style.SUCCESS(f'✅ Cleaned up {deleted_users[0]} test records'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error cleaning up test data: {str(e)}'))

# Additional utility functions that can be called from the command

def send_test_order_confirmation():
    """
    Utility function to send a test order confirmation
    Can be imported and used in views or other places
    """
    try:
        from shop.models import Order
        from shop.email import send_order_confirmation_email
        
        latest_order = Order.objects.first()
        if latest_order:
            return send_order_confirmation_email(latest_order)
        return False
    except Exception as e:
        logger.error(f"Error sending test order confirmation: {str(e)}")
        return False

def send_test_welcome_email():
    """
    Utility function to send a test welcome email
    """
    try:
        from shop.models import MnoryUser
        from shop.email import send_customer_welcome_email
        
        latest_customer = MnoryUser.objects.filter(user_type='customer').first()
        if latest_customer:
            return send_customer_welcome_email(latest_customer)
        return False
    except Exception as e:
        logger.error(f"Error sending test welcome email: {str(e)}")
        return False

def send_test_vendor_email():
    """
    Utility function to send a test vendor registration email
    """
    try:
        from shop.models import VendorProfile
        from shop.email import send_vendor_registration_email
        
        latest_vendor = VendorProfile.objects.first()
        if latest_vendor:
            return send_vendor_registration_email(latest_vendor.user, latest_vendor)
        return False
    except Exception as e:
        logger.error(f"Error sending test vendor email: {str(e)}")
        return False