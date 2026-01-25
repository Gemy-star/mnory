# accounts/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.urls import reverse
from django.utils.translation import gettext as _
from .forms import VendorRegistrationForm, CustomerRegistrationForm, LoginForm


def register_vendor(request):
    if request.method == "POST":
        form = VendorRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, _("Vendor account created successfully."))
            login(request, user)
            return _redirect_by_role(user)  # ✅ use role-based redirect
    else:
        form = VendorRegistrationForm()

    context = {
        "form": form,
        "title": _("Vendor Registration"),
        "form_action": request.path,
        "submit_label": _("Register as Vendor"),
    }
    return render(request, "accounts/vendor_register.html", context)


def register_customer(request):
    if request.method == "POST":
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, _("Customer account created successfully."))
            login(request, user)
            return _redirect_by_role(user)  # ✅ use role-based redirect
    else:
        form = CustomerRegistrationForm()

    context = {
        "form": form,
        "title": _("Customer Registration"),
        "form_action": request.path,
        "submit_label": _("Register as Customer"),
    }
    return render(request, "accounts/customer_register.html", context)


def login_view(request):
    # Already logged in → redirect by role
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    form = LoginForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, _("Login successful."))

        # ✅ Check if ?next= exists
        next_url = request.POST.get("next") or request.GET.get("next")

        # Filter out admin URLs for non-admin users - redirect based on role instead
        if next_url:
            # Don't redirect to admin unless user is actually admin/superuser
            if "/admin/" in next_url:
                if not (user.is_superuser or getattr(user, "is_admin_type", False)):
                    # Non-admin trying to access admin, redirect to their dashboard
                    return _redirect_by_role(user)
            # For other next URLs, allow the redirect
            return redirect(next_url)

        # Otherwise role-based redirect
        return _redirect_by_role(user)

    context = {
        "form": form,
        "title": _("Login"),
        "form_action": reverse("shop:login"),
        "submit_label": _("Log In"),
    }
    return render(request, "accounts/login.html", context)


def _redirect_by_role(user):
    """Redirect user based on role flags - Admins go to custom dashboard"""
    # Debug logging
    import logging

    logger = logging.getLogger(__name__)
    logger.info(
        f"Redirecting user: {user.email}, user_type: {user.user_type}, is_superuser: {user.is_superuser}"
    )

    if getattr(user, "is_vendor_type", False):
        logger.info(f"Redirecting vendor to vendor_dashboard")
        return redirect("shop:vendor_dashboard")
    if getattr(user, "is_freelancer_type", False):
        logger.info(f"Redirecting freelancer to freelancer_dashboard")
        return redirect("freelancing:freelancer_dashboard")
    if getattr(user, "is_company_type", False):
        logger.info(f"Redirecting company to company_dashboard")
        return redirect("freelancing:company_dashboard")
    if getattr(user, "is_customer_type", False):
        logger.info(f"Redirecting customer to profile")
        return redirect("shop:profile")
    if user.is_superuser or getattr(user, "is_admin_type", False):
        # Admin/superusers go to custom admin dashboard
        logger.info(f"Redirecting admin/superuser to admin dashboard")
        return redirect("shop:admin_dashboard")
    logger.info(f"Fallback redirect to home")
    return redirect("shop:home")  # fallback


@login_required
def user_logout(request):
    """Logs out the current user."""
    logout(request)
    messages.info(request, _("You have been logged out."))
    request.session.pop("cart_count", None)  # Clear cart count on logout
    request.session.pop("wishlist_count", None)  # Clear wishlist count on logout
    return redirect("shop:home")
