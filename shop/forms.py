# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import MnoryUser

class RegisterForm(UserCreationForm):
    is_vendor = forms.BooleanField(required=False, label="Register as Vendor")

    class Meta:
        model = MnoryUser
        fields = ['email', 'phone_number', 'password1', 'password2', 'is_vendor']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_vendor = self.cleaned_data.get('is_vendor', False)
        user.is_customer = not user.is_vendor
        if commit:
            user.save()
        return user

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'autofocus': True}))
    password = forms.CharField(widget=forms.PasswordInput)
