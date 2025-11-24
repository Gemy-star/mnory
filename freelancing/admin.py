# freelancing/admin.py - Django Admin Configuration for Freelance Platform
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import models
from .models import *
from .mixins import (
    CompanyFreelancerOnlyMixin,
    SuperuserOnlyMixin,
    FreelancerFilterMixin,
    CompanyFilterMixin,
    ProjectFilterMixin,
    ProposalFilterMixin,
    ContractFilterMixin,
    UserEmailMixin,
    ClientFreelancerEmailMixin,
    FreelancerVerificationMixin,
    ProjectFeatureMixin,
    CountDisplayMixin,
)

User = get_user_model()


# Inline Classes
class FreelancerProfileInline(admin.StackedInline):
    model = FreelancerProfile
    can_delete = False
    verbose_name_plural = "Freelancer Profile"
    extra = 0
    fields = (
        "title",
        "bio",
        "profile_picture",
        "hourly_rate",
        "experience_level",
        "availability",
        "location",
        "rating",
        "total_jobs_completed",
        "total_earnings",
        "is_verified",
    )
    readonly_fields = ("rating", "total_jobs_completed", "total_earnings")


class CompanyProfileInline(admin.StackedInline):
    model = CompanyProfile
    can_delete = False
    verbose_name_plural = "Company Profile"
    extra = 0
    fields = (
        "company_name",
        "description",
        "logo",
        "website_url",
        "industry",
        "company_size",
        "location",
        "founded_year",
        "rating",
        "total_jobs_posted",
        "total_spent",
        "is_verified",
    )
    readonly_fields = ("rating", "total_jobs_posted", "total_spent")


# Category Admin
@admin.register(Category)
class CategoryAdmin(SuperuserOnlyMixin, CountDisplayMixin, admin.ModelAdmin):
    list_display = ("name", "slug", "skills_count", "projects_count", "created_at")
    list_filter = ("created_at",)
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at",)


# Skill Admin
@admin.register(Skill)
class SkillAdmin(SuperuserOnlyMixin, CountDisplayMixin, admin.ModelAdmin):
    list_display = ("name", "category", "freelancers_count", "projects_count")
    list_filter = ("category",)
    search_fields = ("name",)


# Freelancer Profile Admin
@admin.register(FreelancerProfile)
class FreelancerProfileAdmin(
    CompanyFreelancerOnlyMixin,
    FreelancerFilterMixin,
    UserEmailMixin,
    FreelancerVerificationMixin,
    admin.ModelAdmin,
):
    list_display = (
        "user_email",
        "title",
        "experience_level",
        "hourly_rate",
        "rating",
        "total_jobs_completed",
        "is_verified",
        "created_at",
    )
    list_filter = ("experience_level", "availability", "is_verified", "created_at")
    search_fields = ("user__email", "user__first_name", "user__last_name", "title")
    readonly_fields = (
        "rating",
        "total_jobs_completed",
        "total_earnings",
        "created_at",
        "updated_at",
    )
    filter_horizontal = ("skills",)

    fieldsets = (
        ("Basic Info", {"fields": ("user", "title", "bio", "profile_picture")}),
        (
            "Professional Details",
            {"fields": ("hourly_rate", "skills", "experience_level", "availability")},
        ),
        (
            "Contact & Social",
            {
                "fields": (
                    "location",
                    "languages",
                    "portfolio_url",
                    "linkedin_url",
                    "github_url",
                )
            },
        ),
        (
            "Statistics",
            {
                "fields": (
                    "rating",
                    "total_jobs_completed",
                    "total_earnings",
                    "is_verified",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if request.user.is_freelancer_type and obj and obj.user != request.user:
            readonly_fields.extend(["user", "is_verified"])
        return readonly_fields


# Company Profile Admin
@admin.register(CompanyProfile)
class CompanyProfileAdmin(
    CompanyFreelancerOnlyMixin, CompanyFilterMixin, UserEmailMixin, admin.ModelAdmin
):
    list_display = (
        "company_name",
        "user_email",
        "industry",
        "company_size",
        "rating",
        "total_jobs_posted",
        "is_verified",
        "created_at",
    )
    list_filter = ("industry", "company_size", "is_verified", "created_at")
    search_fields = ("company_name", "user__email", "industry", "location")
    readonly_fields = (
        "rating",
        "total_jobs_posted",
        "total_spent",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Basic Info", {"fields": ("user", "company_name", "description", "logo")}),
        (
            "Company Details",
            {
                "fields": (
                    "website_url",
                    "industry",
                    "company_size",
                    "location",
                    "founded_year",
                )
            },
        ),
        (
            "Statistics",
            {
                "fields": ("rating", "total_jobs_posted", "total_spent", "is_verified"),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if request.user.is_company_type and obj and obj.user != request.user:
            readonly_fields.extend(["user", "is_verified"])
        return readonly_fields


# Project Admin
@admin.register(Project)
class ProjectAdmin(
    CompanyFreelancerOnlyMixin,
    ProjectFilterMixin,
    ProjectFeatureMixin,
    admin.ModelAdmin,
):
    list_display = (
        "title",
        "client_email",
        "category",
        "project_type",
        "status",
        "budget_display",
        "proposals_count",
        "views_count",
        "created_at",
    )
    list_filter = (
        "status",
        "project_type",
        "experience_level",
        "category",
        "created_at",
    )
    search_fields = ("title", "description", "client__email")
    readonly_fields = ("views_count", "proposals_count", "created_at", "updated_at")
    filter_horizontal = ("skills_required",)
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Basic Info",
            {"fields": ("title", "description", "client", "category", "status")},
        ),
        (
            "Project Details",
            {
                "fields": (
                    "skills_required",
                    "project_type",
                    "experience_level",
                    "estimated_duration",
                    "deadline",
                )
            },
        ),
        (
            "Budget",
            {
                "fields": (
                    "budget_min",
                    "budget_max",
                    "hourly_rate_min",
                    "hourly_rate_max",
                )
            },
        ),
        ("Media", {"fields": ("attachments", "is_featured")}),
        (
            "Statistics",
            {"fields": ("views_count", "proposals_count"), "classes": ("collapse",)},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def client_email(self, obj):
        return obj.client.email

    client_email.short_description = "Client Email"
    client_email.admin_order_field = "client__email"

    def budget_display(self, obj):
        if obj.project_type == "fixed":
            return f"${obj.budget_min} - ${obj.budget_max}"
        else:
            return f"${obj.hourly_rate_min} - ${obj.hourly_rate_max}/hr"

    budget_display.short_description = "Budget"

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if request.user.is_freelancer_type:
            readonly_fields.extend(["client", "status", "is_featured"])
        return readonly_fields


# Proposal Admin
@admin.register(Proposal)
class ProposalAdmin(CompanyFreelancerOnlyMixin, ProposalFilterMixin, admin.ModelAdmin):
    list_display = (
        "project_title",
        "freelancer_email",
        "proposed_amount",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "project__title",
        "freelancer__email",
        "freelancer__first_name",
        "freelancer__last_name",
    )
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"

    def project_title(self, obj):
        return obj.project.title

    project_title.short_description = "Project"
    project_title.admin_order_field = "project__title"

    def freelancer_email(self, obj):
        return obj.freelancer.email

    freelancer_email.short_description = "Freelancer"
    freelancer_email.admin_order_field = "freelancer__email"

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if request.user.is_freelancer_type:
            readonly_fields.extend(["freelancer", "status"])
        elif request.user.is_company_type:
            readonly_fields.extend(
                ["freelancer", "project", "proposed_amount", "cover_letter"]
            )
        return readonly_fields


# Contract Admin
@admin.register(Contract)
class ContractAdmin(
    CompanyFreelancerOnlyMixin,
    ContractFilterMixin,
    ClientFreelancerEmailMixin,
    admin.ModelAdmin,
):
    list_display = (
        "title",
        "client_email",
        "freelancer_email",
        "amount",
        "status",
        "start_date",
        "end_date",
    )
    list_filter = ("status", "start_date", "end_date")
    search_fields = ("title", "client__email", "freelancer__email")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "start_date"

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if request.user.is_freelancer_type:
            readonly_fields.extend(["client", "amount"])
        elif request.user.is_company_type:
            readonly_fields.extend(["freelancer"])
        return readonly_fields


# Payment Admin
@admin.register(Payment)
class PaymentAdmin(CompanyFreelancerOnlyMixin, admin.ModelAdmin):
    list_display = (
        "contract_title",
        "amount",
        "payment_type",
        "status",
        "due_date",
        "paid_date",
        "created_at",
    )
    list_filter = ("payment_type", "status", "created_at", "due_date")
    search_fields = ("contract__title", "description", "transaction_id")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"

    def contract_title(self, obj):
        return obj.contract.title

    contract_title.short_description = "Contract"
    contract_title.admin_order_field = "contract__title"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_admin_type:
            return qs
        elif request.user.is_company_type:
            return qs.filter(contract__client=request.user)
        elif request.user.is_freelancer_type:
            return qs.filter(contract__freelancer=request.user)
        return qs.none()


# Review Admin
@admin.register(Review)
class ReviewAdmin(CompanyFreelancerOnlyMixin, admin.ModelAdmin):
    list_display = (
        "contract_title",
        "reviewer_email",
        "reviewee_email",
        "rating",
        "is_public",
        "created_at",
    )
    list_filter = ("rating", "is_public", "created_at")
    search_fields = ("contract__title", "reviewer__email", "reviewee__email", "comment")
    readonly_fields = ("created_at",)

    def contract_title(self, obj):
        return obj.contract.title

    contract_title.short_description = "Contract"

    def reviewer_email(self, obj):
        return obj.reviewer.email

    reviewer_email.short_description = "Reviewer"

    def reviewee_email(self, obj):
        return obj.reviewee.email

    reviewee_email.short_description = "Reviewee"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_admin_type:
            return qs
        else:
            return qs.filter(
                models.Q(reviewer=request.user) | models.Q(reviewee=request.user)
            )


# Message Admin
@admin.register(Message)
class MessageAdmin(CompanyFreelancerOnlyMixin, admin.ModelAdmin):
    list_display = (
        "subject",
        "sender_email",
        "recipient_email",
        "is_read",
        "created_at",
    )
    list_filter = ("is_read", "created_at")
    search_fields = ("subject", "message", "sender__email", "recipient__email")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"

    def sender_email(self, obj):
        return obj.sender.email

    sender_email.short_description = "From"

    def recipient_email(self, obj):
        return obj.recipient.email

    recipient_email.short_description = "To"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_admin_type:
            return qs
        else:
            return qs.filter(
                models.Q(sender=request.user) | models.Q(recipient=request.user)
            )


# Notification Admin
@admin.register(Notification)
class NotificationAdmin(CompanyFreelancerOnlyMixin, admin.ModelAdmin):
    list_display = ("title", "user_email", "notification_type", "is_read", "created_at")
    list_filter = ("notification_type", "is_read", "created_at")
    search_fields = ("title", "message", "user__email")
    readonly_fields = ("created_at",)

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = "User Email"
    user_email.admin_order_field = "user__email"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_admin_type:
            return qs
        else:
            return qs.filter(user=request.user)
