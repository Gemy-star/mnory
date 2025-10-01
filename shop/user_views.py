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
            return redirect(reverse('admin:index'))
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
            return redirect('shop:home')
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
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    form = LoginForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            user = authenticate(request, email=email, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, _("Login successful."))

                # ✅ If ?next= exists → go there
                next_url = request.POST.get("next") or request.GET.get("next")
                if next_url:
                    return redirect(next_url)

                return _redirect_by_role(user)

            else:
                messages.error(request, _("Invalid email or password."))

    context = {
        "form": form,
        "title": _("Login"),
        "form_action": request.path,
        "submit_label": _("Log In"),
    }
    return render(request, "accounts/login.html", context)


def _redirect_by_role(user):
    """Helper: redirect based on role flags"""
    if getattr(user, "is_vendor_type", False):
        return redirect(reverse("shop_admin:index"))
    if getattr(user, "is_admin_type", False):
        return redirect(reverse("admin:index"))
    if getattr(user, "is_freelancer_type", False) or getattr(user, "is_company_type", False):
        return redirect(reverse("freelancing_admin:index"))
    if getattr(user, "is_customer_type", False):
        return redirect(reverse("shop:home"))
    return redirect(reverse("shop:home"))  # fallback

@login_required
def user_logout(request):
    """Logs out the current user."""
    logout(request)
    messages.info(request, _("You have been logged out."))
    request.session.pop('cart_count', None)  # Clear cart count on logout
    request.session.pop('wishlist_count', None)  # Clear wishlist count on logout
    return redirect('shop:home')
