from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from .models import ShippingAddress, VendorProfile

MnoryUser = get_user_model()

class RegisterForm(UserCreationForm):
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        help_text="Optional: Your phone number (e.g., +1234567890)",
        widget=forms.TextInput(attrs={'placeholder': 'Phone Number', 'class': 'form-control'})
    )

    user_type = forms.ChoiceField(
        choices=MnoryUser.USER_TYPE_CHOICES,
        required=True,
        initial='customer',
        widget=forms.HiddenInput(),
        help_text="Select your user type."
    )

    class Meta(UserCreationForm.Meta):
        model = MnoryUser
        fields = UserCreationForm.Meta.fields + ('email', 'phone_number', 'user_type',)
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email', 'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Phone Number', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            if field_name != 'password2':
                self.fields[field_name].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].required = True

    def save(self, commit=True):
        user = super().save(commit=False)
        user.phone_number = self.cleaned_data.get('phone_number')
        user.user_type = self.cleaned_data.get('user_type', 'customer')
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Username or Email', 'class': 'form-control'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].required = True
        self.fields['password'].required = True


class ShippingAddressForm(forms.ModelForm):
    class Meta:
        model = ShippingAddress
        fields = [
            'full_name', 'address_line1', 'address_line2', 'city', 'phone_number', 'is_default', 'email'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Full Name')}),
            'address_line1': forms.Textarea(attrs={'class': 'form-control', 'placeholder': _('Address Line 1')}),
            'address_line2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Address Line 2 (Optional)')}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('City')}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Email')}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Phone Number')}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'full_name': _('Full Name'),
            'address_line1': _('Address Line 1'),
            'address_line2': _('Address Line 2'),
            'phone_number': _('Phone Number'),
            'is_default': _('Set as default address'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault('class', 'form-check-input')
            else:
                field.widget.attrs.setdefault('class', 'form-control')


class PaymentForm(forms.Form):
    PAYMENT_CHOICES = [
        ('cod', _('Cash on Delivery')),
    ]

    payment_method = forms.ChoiceField(
        choices=PAYMENT_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label=_("Select Payment Method")
    )


class VendorRegistrationForm(UserCreationForm):
    store_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Store Name'}))
    store_description = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), required=False)
    website = forms.URLField(widget=forms.URLInput(attrs={'class': 'form-control'}), required=False)
    logo = forms.ImageField(widget=forms.ClearableFileInput(attrs={'class': 'form-control'}), required=False)
    country_of_operation = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), required=False)

    class Meta:
        model = MnoryUser
        fields = ['email', 'phone_number', 'password1', 'password2']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'vendor'
        if commit:
            user.save()
            VendorProfile.objects.create(
                user=user,
                store_name=self.cleaned_data['store_name'],
                store_description=self.cleaned_data.get('store_description'),
                website=self.cleaned_data.get('website'),
                logo=self.cleaned_data.get('logo'),
                country_of_operation=self.cleaned_data.get('country_of_operation'),
            )
        return user


class CustomerRegistrationForm(UserCreationForm):
    class Meta:
        model = MnoryUser
        fields = ['email', 'phone_number', 'password1', 'password2']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'customer'
        if commit:
            user.save()
        return user


class VendorProfileForm(forms.ModelForm):
    class Meta:
        model = VendorProfile
        fields = ['store_name', 'store_description', 'logo', 'website', 'country_of_operation']
        widgets = {
            'store_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Store Name'}),
            'store_description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Describe your store...', 'rows': 4}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com'}),
            'country_of_operation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),
        }


class MnoryUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = MnoryUser
        fields = ('username', 'email', 'phone_number', 'user_type', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

    def clean_username(self):
        username = self.cleaned_data['username']
        if self.Meta.model.objects.filter(username=username).exists():
            raise forms.ValidationError(_("A user with that username already exists."))
        return username


class MnoryUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = MnoryUser
        fields = (
            'username', 'first_name', 'last_name', 'email', 'phone_number', 'user_type',
            'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions',
            'last_login', 'date_joined'
        )
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'user_type': forms.Select(attrs={'class': 'form-select'}),
        }


# Optional: simplified login form (not using AuthenticationForm)
class SimpleLoginForm(forms.Form):
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Email')})
    )
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Password')})
    )
