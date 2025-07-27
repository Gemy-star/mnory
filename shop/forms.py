# shop/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import MnoryUser, ShippingAddress, Payment, Order, VendorProfile
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

class RegisterForm(UserCreationForm):
    """
    Form for user registration, extending Django's built-in UserCreationForm.
    Includes custom fields from MnoryUser model.
    """
    phone = forms.CharField(
        max_length=15,
        required=False,
        help_text="Optional: Your phone number (e.g., +1234567890)"
    )
    is_customer = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.HiddenInput(),
        help_text="Indicates if the user is a customer."
    )

    class Meta(UserCreationForm.Meta):
        model = MnoryUser
        fields = ('email', 'password1', 'password2', 'phone', 'is_customer')
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'Email', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove username field since MnoryUser uses email
        if 'username' in self.fields:
            del self.fields['username']
        
        # Add placeholders and styling
        self.fields['email'].widget.attrs.update({
            'placeholder': 'Email Address',
            'class': 'form-control'
        })
        self.fields['password1'].widget.attrs.update({
            'placeholder': 'Password',
            'class': 'form-control'
        })
        self.fields['password2'].widget.attrs.update({
            'placeholder': 'Confirm Password',
            'class': 'form-control'
        })
        self.fields['phone'].widget.attrs.update({
            'placeholder': 'Phone Number (Optional)',
            'class': 'form-control'
        })


class VendorRegisterForm(UserCreationForm):
    """
    Form for vendor registration, extending Django's built-in UserCreationForm.
    Creates both MnoryUser and VendorProfile.
    """
    phone = forms.CharField(
        max_length=15,
        required=False,
        help_text="Optional: Your phone number (e.g., +1234567890)"
    )
    
    # Vendor-specific fields
    store_name = forms.CharField(
        max_length=255,
        required=True,
        help_text="Enter your store/business name"
    )
    store_description = forms.CharField(
        widget=forms.Textarea(),
        required=False,
        help_text="Optional: Describe your store and products"
    )
    website = forms.URLField(
        required=False,
        help_text="Optional: Your store website URL"
    )
    country_of_operation = forms.CharField(
        max_length=200,
        required=False,
        help_text="Optional: Country where you operate your business"
    )

    class Meta(UserCreationForm.Meta):
        model = MnoryUser
        fields = ('email', 'password1', 'password2', 'phone')
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'Email', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove username field since MnoryUser uses email
        if 'username' in self.fields:
            del self.fields['username']
        
        # Add placeholders and styling
        self.fields['email'].widget.attrs.update({
            'placeholder': 'Email Address',
            'class': 'form-control'
        })
        self.fields['password1'].widget.attrs.update({
            'placeholder': 'Password',
            'class': 'form-control'
        })
        self.fields['password2'].widget.attrs.update({
            'placeholder': 'Confirm Password',
            'class': 'form-control'
        })
        self.fields['phone'].widget.attrs.update({
            'placeholder': 'Phone Number (Optional)',
            'class': 'form-control'
        })
        self.fields['store_name'].widget.attrs.update({
            'placeholder': 'Store Name',
            'class': 'form-control'
        })
        self.fields['store_description'].widget.attrs.update({
            'placeholder': 'Describe your store and products...',
            'class': 'form-control'
        })
        self.fields['website'].widget.attrs.update({
            'placeholder': 'https://yourstore.com',
            'class': 'form-control'
        })
        self.fields['country_of_operation'].widget.attrs.update({
            'placeholder': 'Country of Operation',
            'class': 'form-control'
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_vendor = True
        user.is_customer = False
        if commit:
            user.save()
            # Create vendor profile
            VendorProfile.objects.create(
                user=user,
                store_name=self.cleaned_data['store_name'],
                store_description=self.cleaned_data.get('store_description', ''),
                website=self.cleaned_data.get('website', ''),
                country_of_operation=self.cleaned_data.get('country_of_operation', ''),
            )
        return user


class LoginForm(AuthenticationForm):
    """
    Custom login form that works with email instead of username.
    """
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'Email Address', 
            'class': 'form-control',
            'autofocus': True
        }),
        label="Email"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Password', 
            'class': 'form-control'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].required = True
        self.fields['password'].required = True

    class Meta:
        model = MnoryUser


class VendorProfileForm(forms.ModelForm):
    """
    Form for updating vendor profile information.
    """
    class Meta:
        model = VendorProfile
        fields = [
            'store_name', 'store_description', 'logo', 'website', 
            'country_of_operation'
        ]
        widgets = {
            'store_name': forms.TextInput(attrs={
                'placeholder': 'Store Name', 
                'class': 'form-control'
            }),
            'store_description': forms.Textarea(attrs={
                'placeholder': 'Describe your store and products...', 
                'class': 'form-control',
                'rows': 4
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'website': forms.URLInput(attrs={
                'placeholder': 'https://yourstore.com', 
                'class': 'form-control'
            }),
            'country_of_operation': forms.TextInput(attrs={
                'placeholder': 'Country of Operation', 
                'class': 'form-control'
            }),
        }


class ShippingAddressForm(forms.ModelForm):
    """
    Form for collecting shipping address details.
    Includes a checkbox to save the address as default for the user.
    Country is fixed to Egypt.
    """
    country = forms.CharField(
        widget=forms.HiddenInput(),
        initial='EG'  # Egypt country code
    )

    save_as_default = forms.BooleanField(
        required=False,
        initial=False,
        label="Save this address as my default for future orders",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = ShippingAddress
        exclude = ('order', 'is_default')
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Full Name', 'class': 'form-control'}),
            'address_line1': forms.TextInput(attrs={'placeholder': 'Address Line 1', 'class': 'form-control'}),
            'address_line2': forms.TextInput(attrs={'placeholder': 'Address Line 2 (Optional)', 'class': 'form-control'}),
            'city': forms.TextInput(attrs={'placeholder': 'City', 'class': 'form-control'}),
            'state_province_region': forms.TextInput(attrs={'placeholder': 'State/Province/Region (Optional)', 'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'placeholder': 'Postal Code (Optional)', 'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Phone Number', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['save_as_default', 'country']:
                field.widget.attrs.setdefault('class', 'form-control')


class PaymentForm(forms.Form):
    PAYMENT_CHOICES = [
        ('cod', 'Cash on Delivery'),
        # ('visa', 'Visa (Coming Soon)'),  # Uncomment to add Visa later
    ]

    payment_method = forms.ChoiceField(
        choices=PAYMENT_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Select Payment Method"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment_method'].widget.attrs.update({'class': 'form-check-input'})