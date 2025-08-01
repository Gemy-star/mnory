# middleware.py
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin


class AdminAccessMiddleware(MiddlewareMixin):
    """
    Middleware to control admin access based on user type
    """

    def process_request(self, request):
        # Check if this is an admin URL
        if request.path.startswith('/admin/'):
            # Allow login and logout pages
            if request.path in ['/admin/login/', '/admin/logout/']:
                return None

            # Check if user is authenticated
            if not request.user.is_authenticated:
                return None  # Let Django handle redirect to login

            # Get user type
            user_type = getattr(request.user, 'user_type', None)

            # Allow superusers and staff
            if request.user.is_superuser or request.user.is_staff:
                return None

            # Check if user has allowed user_type for admin access
            allowed_user_types = ['vendor', 'customer', 'client']
            if user_type not in allowed_user_types:
                messages.error(request, 'You do not have permission to access the admin panel.')
                logout(request)
                return redirect('admin:login')

            # Additional check for vendor approval
            if user_type == 'vendor':
                try:
                    from shop.models import VendorProfile
                    vendor_profile = VendorProfile.objects.get(user=request.user)
                    if not vendor_profile.is_approved:
                        messages.warning(request,
                                         'Your vendor account is pending approval. Some features may be limited.')
                except VendorProfile.DoesNotExist:
                    if '/admin/shop/vendorprofile/add/' not in request.path:
                        messages.info(request, 'Please complete your vendor profile setup.')
                        return redirect('/admin/shop/vendorprofile/add/')

        return None


class UserTypeContextMiddleware(MiddlewareMixin):
    """
    Middleware to add user type context to all requests
    """

    def process_request(self, request):
        if request.user.is_authenticated:
            request.user_type = getattr(request.user, 'user_type', 'admin')
            request.is_vendor = request.user_type == 'vendor'
            request.is_customer = request.user_type in ['customer', 'client']
            request.is_admin = request.user.is_superuser or request.user.is_staff
        else:
            request.user_type = None
            request.is_vendor = False
            request.is_customer = False
            request.is_admin = False

        return None