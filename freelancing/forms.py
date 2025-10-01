from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError
from django.utils.translation import gettext_lazy as _
from shop.models import MnoryUser as User
from .models import *


class CompanyRegistrationForm(UserCreationForm):
    company_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company Name'})
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe your company'}),
        required=False
    )
    logo = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}), required=False
    )
    website_url = forms.URLField(
        widget=forms.URLInput(attrs={'class': 'form-control'}), required=False
    )
    industry = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Industry'}), required=False
    )
    company_size = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company Size'}), required=False
    )
    location = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location'}), required=False
    )
    founded_year = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Founded Year'}), required=False
    )

    class Meta:
        model = User
        fields = ['email', 'phone_number', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'company'
        if commit:
            try:
                with transaction.atomic():
                    user.save()
                    CompanyProfile.objects.get_or_create(
                        user=user,
                        defaults={
                            'company_name': self.cleaned_data['company_name'],
                            'description': self.cleaned_data.get('description'),
                            'logo': self.cleaned_data.get('logo'),
                            'website_url': self.cleaned_data.get('website_url'),
                            'industry': self.cleaned_data.get('industry'),
                            'company_size': self.cleaned_data.get('company_size'),
                            'location': self.cleaned_data.get('location'),
                            'founded_year': self.cleaned_data.get('founded_year'),
                        }
                    )
            except IntegrityError:
                raise forms.ValidationError(_("A company profile already exists for this user."))
        return user


class FreelancerRegistrationForm(UserCreationForm):
    title = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Title (e.g., Full Stack Dev)'})
    )
    bio = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Tell clients about yourself'}),
        required=False
    )
    profile_picture = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}), required=False
    )
    hourly_rate = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 5, 'max': 500, 'step': 0.01})
    )
    skills = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Skills'}), required=False
    )
    languages = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Languages'}), required=False
    )
    experience_level = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Experience Level'}), required=False
    )
    portfolio_url = forms.URLField(
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Portfolio URL'}), required=False
    )
    linkedin_url = forms.URLField(
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'LinkedIn URL'}), required=False
    )
    github_url = forms.URLField(
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'GitHub URL'}), required=False
    )
    location = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location'}), required=False
    )
    availability = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Availability'}), required=False
    )

    class Meta:
        model = User
        fields = ['email', 'phone_number', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'freelancer'
        if commit:
            try:
                with transaction.atomic():
                    user.save()
                    FreelancerProfile.objects.get_or_create(
                        user=user,
                        defaults={
                            'title': self.cleaned_data['title'],
                            'bio': self.cleaned_data.get('bio'),
                            'profile_picture': self.cleaned_data.get('profile_picture'),
                            'hourly_rate': self.cleaned_data.get('hourly_rate'),
                            'skills': self.cleaned_data.get('skills'),
                            'languages': self.cleaned_data.get('languages'),
                            'experience_level': self.cleaned_data.get('experience_level'),
                            'portfolio_url': self.cleaned_data.get('portfolio_url'),
                            'linkedin_url': self.cleaned_data.get('linkedin_url'),
                            'github_url': self.cleaned_data.get('github_url'),
                            'location': self.cleaned_data.get('location'),
                            'availability': self.cleaned_data.get('availability'),
                        }
                    )
            except IntegrityError:
                raise forms.ValidationError(_("A freelancer profile already exists for this user."))
        return user
class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'title', 'description', 'category', 'skills_required',
            'project_type', 'budget_min', 'budget_max', 'hourly_rate_min',
            'hourly_rate_max', 'estimated_duration', 'experience_level',
            'deadline', 'attachments'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Build a Mobile App for Restaurant Orders'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Provide a detailed description of your project...'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'skills_required': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'project_type': forms.RadioSelect(attrs={
                'class': 'form-check-input'
            }),
            'budget_min': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 50,
                'step': 0.01
            }),
            'budget_max': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 50,
                'step': 0.01
            }),
            'hourly_rate_min': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 5,
                'step': 0.01
            }),
            'hourly_rate_max': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 5,
                'step': 0.01
            }),
            'estimated_duration': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2-3 weeks, 1 month'
            }),
            'experience_level': forms.Select(attrs={
                'class': 'form-select'
            }),
            'deadline': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'attachments': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.txt,.zip'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        project_type = cleaned_data.get('project_type')

        if project_type == 'fixed':
            budget_min = cleaned_data.get('budget_min')
            budget_max = cleaned_data.get('budget_max')

            if not budget_min or not budget_max:
                raise ValidationError("Budget range is required for fixed price projects")

            if budget_min > budget_max:
                raise ValidationError("Minimum budget cannot be greater than maximum budget")

        elif project_type == 'hourly':
            hourly_min = cleaned_data.get('hourly_rate_min')
            hourly_max = cleaned_data.get('hourly_rate_max')

            if not hourly_min or not hourly_max:
                raise ValidationError("Hourly rate range is required for hourly projects")

            if hourly_min > hourly_max:
                raise ValidationError("Minimum hourly rate cannot be greater than maximum hourly rate")

        return cleaned_data

    def clean_description(self):
        description = self.cleaned_data['description']
        if len(description) < 100:
            raise ValidationError("Project description must be at least 100 characters long")
        return description


class ProposalForm(forms.ModelForm):
    class Meta:
        model = Proposal
        fields = ['cover_letter', 'proposed_amount', 'estimated_duration', 'attachments']
        widgets = {
            'cover_letter': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Explain why you are the best fit for this project...'
            }),
            'proposed_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'step': 0.01,
                'placeholder': 'Enter your proposed amount'
            }),
            'estimated_duration': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2 weeks, 1 month'
            }),
            'attachments': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.txt,.zip'
            }),
        }

    def clean_cover_letter(self):
        cover_letter = self.cleaned_data['cover_letter']
        if len(cover_letter) < 100:
            raise ValidationError("Cover letter must be at least 100 characters long")
        return cover_letter

    def clean_proposed_amount(self):
        amount = self.cleaned_data['proposed_amount']
        if amount < 1:
            raise ValidationError("Proposed amount must be at least $1")
        return amount


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['subject', 'message', 'attachment']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Message subject'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Type your message here...'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.txt,.zip,.jpg,.jpeg,.png'
            }),
        }

    def clean_message(self):
        message = self.cleaned_data['message']
        if len(message.strip()) < 10:
            raise ValidationError("Message must be at least 10 characters long")
        return message


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment', 'is_public']
        widgets = {
            'rating': forms.RadioSelect(attrs={
                'class': 'form-check-input'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Share your experience working with this person...'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rating'].choices = [(i, f"{i} Star{'s' if i != 1 else ''}") for i in range(1, 6)]

    def clean_comment(self):
        comment = self.cleaned_data['comment']
        if len(comment.strip()) < 20:
            raise ValidationError("Review comment must be at least 20 characters long")
        return comment


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'payment_type', 'description', 'due_date']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'step': 0.01
            }),
            'payment_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Payment description or milestone details...'
            }),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
        }


class ProjectSearchForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search projects...'
        })
    )

    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    project_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Project.PROJECT_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    experience_level = forms.ChoiceField(
        choices=[('', 'All Levels')] + Project.EXPERIENCE_LEVEL_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    min_budget = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min budget'
        })
    )

    max_budget = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Max budget'
        })
    )

    sort_by = forms.ChoiceField(
        choices=[
            ('-created_at', 'Newest First'),
            ('created_at', 'Oldest First'),
            ('-budget_max', 'Highest Budget'),
            ('budget_max', 'Lowest Budget'),
            ('-proposals_count', 'Most Proposals'),
            ('proposals_count', 'Least Proposals'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class FreelancerSearchForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search freelancers...'
        })
    )

    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )

    experience_level = forms.ChoiceField(
        choices=[('', 'All Levels')] + FreelancerProfile.experience_level.field.choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    min_rate = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min hourly rate'
        })
    )

    max_rate = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Max hourly rate'
        })
    )

    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Location'
        })
    )

    availability = forms.ChoiceField(
        choices=[('', 'Any Availability')] + FreelancerProfile.availability.field.choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    min_rating = forms.DecimalField(
        required=False,
        max_digits=3,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min rating',
            'min': 0,
            'max': 5,
            'step': 0.1
        })
    )

    verified_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    sort_by = forms.ChoiceField(
        choices=[
            ('-rating', 'Highest Rated'),
            ('rating', 'Lowest Rated'),
            ('-hourly_rate', 'Highest Rate'),
            ('hourly_rate', 'Lowest Rate'),
            ('-total_jobs_completed', 'Most Experience'),
            ('total_jobs_completed', 'Least Experience'),
            ('-created_at', 'Newest Members'),
            ('created_at', 'Oldest Members'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class ContractUpdateForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = ['status', 'end_date', 'terms_and_conditions']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'terms_and_conditions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6
            }),
        }


class BulkMessageForm(forms.Form):
    recipients = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),  # Will be set in __init__
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label="Recipients"
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 6})
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set queryset based on user type
        if user.is_company_user:
            # Companies can message freelancers they've worked with
            self.fields['recipients'].queryset = User.objects.filter(
                contracts_as_freelancer__client=user
            ).distinct()
        elif user.is_freelancer_user:
            # Freelancers can message companies they've worked with
            self.fields['recipients'].queryset = User.objects.filter(
                contracts_as_client__freelancer=user
            ).distinct()


class AdvancedProjectFilterForm(forms.Form):
    # Location-based filtering
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Location'
        })
    )

    # Date range filtering
    posted_after = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    posted_before = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    # Proposal count filtering
    max_proposals = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Max proposals'
        })
    )

    # Client type filtering
    verified_clients_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    # Client rating filtering
    min_client_rating = forms.DecimalField(
        required=False,
        max_digits=3,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 0,
            'max': 5,
            'step': 0.1
        })
    )


class ReportForm(forms.Form):
    REPORT_TYPES = [
        ('earnings', 'Earnings Report'),
        ('projects', 'Projects Report'),
        ('performance', 'Performance Report'),
        ('activity', 'Activity Report'),
    ]

    report_type = forms.ChoiceField(
        choices=REPORT_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    end_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    format = forms.ChoiceField(
        choices=[('pdf', 'PDF'), ('csv', 'CSV'), ('excel', 'Excel')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class DisputeForm(forms.Form):
    DISPUTE_TYPES = [
        ('payment', 'Payment Issue'),
        ('quality', 'Work Quality Issue'),
        ('communication', 'Communication Problem'),
        ('scope', 'Scope Disagreement'),
        ('other', 'Other')
    ]

    dispute_type = forms.ChoiceField(
        choices=DISPUTE_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Describe the issue in detail...'
        })
    )

    evidence = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.zip'
        })
    )

    def clean_description(self):
        description = self.cleaned_data['description']
        if len(description.strip()) < 50:
            raise ValidationError("Description must be at least 50 characters long")
        return description


class MilestoneForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['description', 'amount', 'due_date']
        widgets = {
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Milestone description'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'step': 0.01
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }


class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ['name', 'category']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'slug']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
        }


class WithdrawalRequestForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=10,  # Minimum withdrawal amount
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Amount to withdraw'
        })
    )

    withdrawal_method = forms.ChoiceField(
        choices=[
            ('bank_transfer', 'Bank Transfer'),
            ('paypal', 'PayPal'),
            ('stripe', 'Stripe'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    account_details = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Bank account details or PayPal email'
        })
    )

    def __init__(self, available_balance, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.available_balance = available_balance

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount > self.available_balance:
            raise ValidationError(f"Amount cannot exceed available balance of ${self.available_balance}")
        return amount


class TeamInviteForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    role = forms.ChoiceField(
        choices=[
            ('member', 'Team Member'),
            ('manager', 'Project Manager'),
            ('admin', 'Administrator'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional invitation message'
        })
    )