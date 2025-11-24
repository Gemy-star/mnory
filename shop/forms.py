from django import forms
from django.contrib.auth.forms import (
    UserCreationForm,
    AuthenticationForm,
    UserChangeForm,
)
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from .models import *
from .consts import get_group_for_user_type
from django.db import transaction, IntegrityError

MnoryUser = get_user_model()


class RegisterForm(UserCreationForm):
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        help_text="Optional: Your phone number (e.g., +1234567890)",
        widget=forms.TextInput(
            attrs={"placeholder": "Phone Number", "class": "form-control"}
        ),
    )

    user_type = forms.ChoiceField(
        choices=MnoryUser.USER_TYPE_CHOICES,
        required=True,
        initial="customer",
        widget=forms.HiddenInput(),
        help_text="Select your user type.",
    )

    class Meta(UserCreationForm.Meta):
        model = MnoryUser
        fields = UserCreationForm.Meta.fields + (
            "email",
            "phone_number",
            "user_type",
        )
        widgets = {
            "username": forms.TextInput(
                attrs={"placeholder": "Username", "class": "form-control"}
            ),
            "email": forms.EmailInput(
                attrs={"placeholder": "Email", "class": "form-control"}
            ),
            "phone_number": forms.TextInput(
                attrs={"placeholder": "Phone Number", "class": "form-control"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            if field_name != "password2":
                self.fields[field_name].widget.attrs.update({"class": "form-control"})
        self.fields["email"].required = True

    def save(self, commit=True):
        user = super().save(commit=False)
        user.phone_number = self.cleaned_data.get("phone_number")
        user.user_type = self.cleaned_data.get("user_type", "customer")
        if commit:
            user.save()
            # Assign user to appropriate group
            group_name = get_group_for_user_type(user.user_type)
            if group_name:
                group, _ = Group.objects.get_or_create(name=group_name)
                user.groups.add(group)
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={"placeholder": "Username or Email", "class": "form-control"}
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"placeholder": "Password", "class": "form-control"}
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].required = True
        self.fields["password"].required = True


class ShippingAddressForm(forms.ModelForm):
    CITY_CHOICES = [
        ("", _("Select City")),
        ("INSIDE_CAIRO", _("Inside Cairo")),
        ("OUTSIDE_CAIRO", _("Outside Cairo")),
    ]

    city = forms.ChoiceField(
        choices=CITY_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
        label=_("City"),
    )

    class Meta:
        model = ShippingAddress
        fields = [
            "full_name",
            "address_line1",
            "address_line2",
            "city",
            "phone_number",
            "is_default",
            "email",
        ]
        widgets = {
            "full_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("Full Name")}
            ),
            "address_line1": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Address Line 1"),
                    "rows": 3,
                }
            ),
            "address_line2": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Address Line 2 (Optional)"),
                }
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": _("Email")}
            ),
            "phone_number": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("Phone Number")}
            ),
            "is_default": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "full_name": _("Full Name"),
            "address_line1": _("Address Line 1"),
            "address_line2": _("Address Line 2"),
            "phone_number": _("Phone Number"),
            "is_default": _("Set as default address"),
            "city": _("City"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-check-input")
            else:
                field.widget.attrs.setdefault("class", "form-control")


class PaymentForm(forms.Form):
    PAYMENT_CHOICES = [
        ("cod", _("Cash on Delivery")),
    ]

    payment_method = forms.ChoiceField(
        choices=PAYMENT_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
        label=_("Select Payment Method"),
    )


class VendorRegistrationForm(UserCreationForm):
    store_name = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Store Name"}
        )
    )
    store_description = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        required=False,
    )
    website = forms.URLField(
        widget=forms.URLInput(attrs={"class": "form-control"}), required=False
    )
    logo = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={"class": "form-control"}), required=False
    )
    country_of_operation = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}), required=False
    )

    class Meta:
        model = MnoryUser
        fields = ["email", "phone_number", "password1", "password2"]
        widgets = {
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "Email"}
            ),
            "phone_number": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Phone Number"}
            ),
            "password1": forms.PasswordInput(
                attrs={"class": "form-control", "placeholder": "Password"}
            ),
            "password2": forms.PasswordInput(
                attrs={"class": "form-control", "placeholder": "Confirm Password"}
            ),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = "vendor"
        if commit:
            try:
                with transaction.atomic():
                    user.save()
                    # Avoid duplicate VendorProfile
                    VendorProfile.objects.get_or_create(
                        user=user,
                        defaults={
                            "store_name": self.cleaned_data["store_name"],
                            "store_description": self.cleaned_data.get(
                                "store_description"
                            ),
                            "website": self.cleaned_data.get("website"),
                            "logo": self.cleaned_data.get("logo"),
                            "country_of_operation": self.cleaned_data.get(
                                "country_of_operation"
                            ),
                        },
                    )
                    # Assign user to appropriate group
                    group_name = get_group_for_user_type(user.user_type)
                    if group_name:
                        group, _ = Group.objects.get_or_create(name=group_name)
                        user.groups.add(group)
            except IntegrityError:
                raise forms.ValidationError(
                    _("A vendor profile already exists for this user.")
                )
        return user


class CustomerRegistrationForm(UserCreationForm):
    class Meta:
        model = MnoryUser
        fields = ["email", "phone_number", "password1", "password2"]
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "password1": forms.PasswordInput(attrs={"class": "form-control"}),
            "password2": forms.PasswordInput(attrs={"class": "form-control"}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = "customer"
        if commit:
            user.save()
            # Assign user to appropriate group
            group_name = get_group_for_user_type(user.user_type)
            if group_name:
                group, _ = Group.objects.get_or_create(name=group_name)
                user.groups.add(group)
        return user


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.NumberInput(
                attrs={"type": "hidden"}
            ),  # Will be handled by stars in frontend
            "comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": _("Write your review..."),
                }
            ),
        }
        labels = {"comment": _("Your Review")}


class CouponApplyForm(forms.Form):
    code = forms.CharField(
        label=_("Coupon Code"),
        max_length=50,
        widget=forms.TextInput(attrs={"placeholder": _("Enter your coupon code")}),
    )


class ReviewReplyForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["reply"]
        widgets = {
            "reply": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": _("Write your reply..."),
                }
            ),
        }
        labels = {"reply": ""}


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ["image", "alt_text", "is_main", "is_hover", "order"]
        widgets = {
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "alt_text": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Image description (for SEO)"),
                }
            ),
            "is_main": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_hover": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }


ProductImageFormSet = forms.inlineformset_factory(
    Product,
    ProductImage,
    form=ProductImageForm,
    extra=1,
    can_delete=True,
    can_delete_extra=True,
)


class BaseProductImageFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        main_image_count = 0
        for form in self.forms:
            if not form.is_valid() or form.cleaned_data.get("DELETE", False):
                continue
            if form.cleaned_data.get("is_main"):
                main_image_count += 1

        if main_image_count > 1:
            raise forms.ValidationError(_("You can only select one main image."))


ProductImageFormSet = forms.inlineformset_factory(
    Product,
    ProductImage,
    form=ProductImageForm,
    formset=BaseProductImageFormSet,
    extra=1,
    can_delete=True,
    can_delete_extra=True,
)


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ["color", "size", "stock_quantity", "price_adjustment", "is_available"]
        widgets = {
            "color": forms.Select(attrs={"class": "form-select"}),
            "size": forms.Select(attrs={"class": "form-select"}),
            "stock_quantity": forms.NumberInput(attrs={"class": "form-control"}),
            "price_adjustment": forms.NumberInput(attrs={"class": "form-control"}),
            "is_available": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


ProductVariantFormSet = forms.inlineformset_factory(
    Product,
    ProductVariant,
    form=ProductVariantForm,
    extra=1,
    can_delete=True,
    can_delete_extra=True,
)


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "description",
            "short_description",
            "category",
            "subcategory",
            "brand",
            "fit_type",
            "price",
            "sale_price",
            "is_active",
            "is_available",
            "is_featured",
            "is_best_seller",
            "is_new_arrival",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "short_description": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "subcategory": forms.Select(attrs={"class": "form-select"}),
            "brand": forms.Select(attrs={"class": "form-select"}),
            "fit_type": forms.Select(attrs={"class": "form-select"}),
            "price": forms.NumberInput(attrs={"class": "form-control"}),
            "sale_price": forms.NumberInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_available": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_featured": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_best_seller": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_new_arrival": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": _("Type your message..."),
                }
            )
        }
        labels = {"body": ""}


class ProductBulkEditForm(forms.Form):
    product_ids = forms.ModelMultipleChoiceField(
        queryset=Product.objects.none(), widget=forms.MultipleHiddenInput()
    )
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False)
    brand = forms.ModelChoiceField(queryset=Brand.objects.all(), required=False)
    price = forms.DecimalField(max_digits=10, decimal_places=2, required=False)
    sale_price = forms.DecimalField(max_digits=10, decimal_places=2, required=False)
    is_active = forms.ChoiceField(
        choices=[("", "---"), ("true", "Active"), ("false", "Inactive")], required=False
    )


class VendorShippingForm(forms.ModelForm):
    class Meta:
        model = VendorShipping
        fields = [
            "shipping_rate_cairo",
            "shipping_rate_outside_cairo",
            "free_shipping_threshold",
        ]


class PayoutRequestForm(forms.Form):
    amount = forms.DecimalField(
        label=_("Payout Amount"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("1.00"))],
        widget=forms.NumberInput(
            attrs={"class": "form-control", "placeholder": "e.g., 500.00"}
        ),
    )

    def __init__(self, *args, **kwargs):
        self.vendor_profile = kwargs.pop("vendor_profile", None)
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if self.vendor_profile and amount > self.vendor_profile.wallet_balance:
            raise forms.ValidationError(
                _("You cannot request more than your available wallet balance.")
            )
        return amount


class VendorProfileForm(forms.ModelForm):
    class Meta:
        model = VendorProfile
        fields = [
            "store_name",
            "store_description",
            "logo",
            "website",
            "country_of_operation",
        ]
        widgets = {
            "store_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Store Name"}
            ),
            "store_description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Describe your store...",
                    "rows": 4,
                }
            ),
            "logo": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "website": forms.URLInput(
                attrs={"class": "form-control", "placeholder": "https://example.com"}
            ),
            "country_of_operation": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Country"}
            ),
        }


class MnoryUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = MnoryUser
        fields = (
            "username",
            "email",
            "phone_number",
            "user_type",
            "password1",
            "password2",
        )
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "password1": forms.PasswordInput(attrs={"class": "form-control"}),
            "password2": forms.PasswordInput(attrs={"class": "form-control"}),
        }

    def clean_username(self):
        username = self.cleaned_data["username"]
        if self.Meta.model.objects.filter(username=username).exists():
            raise forms.ValidationError(_("A user with that username already exists."))
        return username


class MnoryUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = MnoryUser
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "user_type",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
            "last_login",
            "date_joined",
        )
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "user_type": forms.Select(attrs={"class": "form-select"}),
        }


# Optional: simplified login form (not using AuthenticationForm)
class SimpleLoginForm(forms.Form):
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": _("Email")}
        ),
    )
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": _("Password")}
        ),
    )
