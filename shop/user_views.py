# accounts/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.urls import reverse
from django.utils.translation import gettext as _
from .forms import VendorRegistrationForm, CustomerRegistrationForm, LoginForm

def register_vendor(request):
    if request.method == 'POST':
        form = VendorRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, _("Vendor account created successfully."))
            login(request, user)
            return _redirect_by_role(user)  # ✅ use role-based redirect
    else:
        form = VendorRegistrationForm()

    context = {
        'form': form,
        'title': _("Vendor Registration"),
        'form_action': request.path,
        'submit_label': _("Register as Vendor"),
    }
    return render(request, 'accounts/vendor_register.html', context)


def register_customer(request):
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, _("Customer account created successfully."))
            login(request, user)
            return _redirect_by_role(user)  # ✅ use role-based redirect
    else:
        form = CustomerRegistrationForm()

    context = {
        'form': form,
        'title': _("Customer Registration"),
        'form_action': request.path,
        'submit_label': _("Register as Customer"),
    }
    return render(request, 'accounts/customer_register.html', context)

def login_view(request):
    # Already logged in → redirect by role
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    form = LoginForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, _("Login successful."))

        # ✅ If ?next= exists → redirect there
        next_url = request.POST.get("next") or request.GET.get("next")
        if next_url:
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
    """Redirect user based on role flags"""
    if getattr(user, "is_vendor_type", False):
        return redirect("shop_admin:index")
    if getattr(user, "is_admin_type", False):
        return redirect("admin:index")
    if getattr(user, "is_freelancer_type", False) or getattr(user, "is_company_type", False):
        return redirect("freelancing_admin:index")
    if getattr(user, "is_customer_type", False):
        return redirect("shop:home")
    return redirect("shop:home")  # fallback
@login_required
def user_logout(request):
    """Logs out the current user."""
    logout(request)
    messages.info(request, _("You have been logged out."))
    request.session.pop('cart_count', None)  # Clear cart count on logout
    request.session.pop('wishlist_count', None)  # Clear wishlist count on logout
    return redirect('shop:home')
