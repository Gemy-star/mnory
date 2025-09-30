# freelancing/mixins.py
from django.contrib import admin
from django.core.exceptions import PermissionDenied


class CompanyFreelancerOnlyMixin:
    """Mixin to restrict admin access to company and freelancer users only"""

    def has_module_permission(self, request):
        return (
                request.user.is_authenticated and
                request.user.is_active and
                (request.user.is_superuser or
                 request.user.is_admin_type or
                 request.user.is_company_type or
                 request.user.is_freelancer_type)
        )

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_module_permission(request)


class SuperuserOnlyMixin:
    """Mixin to restrict admin access to superusers only"""

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


class FreelancerFilterMixin:
    """Mixin to filter queryset for freelancer users only"""

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_admin_type:
            return qs
        elif request.user.is_freelancer_type:
            return qs.filter(user__user_type='freelancer')
        return qs.none()


class CompanyFilterMixin:
    """Mixin to filter queryset for company users only"""

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_admin_type:
            return qs
        elif request.user.is_company_type:
            return qs.filter(user__user_type='company')
        return qs.none()


class ProjectFilterMixin:
    """Mixin to filter projects from company users only"""

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_admin_type:
            return qs
        elif request.user.is_company_type:
            return qs.filter(client=request.user)
        return qs.none()


class ProposalFilterMixin:
    """Mixin to filter proposals from freelancer users only"""

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_admin_type:
            return qs
        elif request.user.is_freelancer_type:
            return qs.filter(freelancer=request.user)
        return qs.none()


class ContractFilterMixin:
    """Mixin to filter contracts between companies and freelancers"""

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_admin_type:
            return qs
        elif request.user.is_company_type:
            return qs.filter(client=request.user)
        elif request.user.is_freelancer_type:
            return qs.filter(freelancer=request.user)
        return qs.none()


class UserEmailMixin:
    """Mixin to add user email display methods"""

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'


class ClientFreelancerEmailMixin:
    """Mixin to add client and freelancer email display methods"""

    def client_email(self, obj):
        return obj.client.email

    client_email.short_description = 'Client Email'
    client_email.admin_order_field = 'client__email'

    def freelancer_email(self, obj):
        return obj.freelancer.email

    freelancer_email.short_description = 'Freelancer Email'
    freelancer_email.admin_order_field = 'freelancer__email'


class FreelancerVerificationMixin:
    """Mixin to add freelancer verification actions"""

    actions = ['verify_freelancers', 'unverify_freelancers']

    def verify_freelancers(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} freelancers were successfully verified.')

    verify_freelancers.short_description = "Verify selected freelancers"

    def unverify_freelancers(self, request, queryset):
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'{updated} freelancers were unverified.')

    unverify_freelancers.short_description = "Unverify selected freelancers"


class ProjectFeatureMixin:
    """Mixin to add project featuring actions"""

    actions = ['feature_projects', 'unfeature_projects']

    def feature_projects(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} projects were featured.')

    feature_projects.short_description = "Feature selected projects"

    def unfeature_projects(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} projects were unfeatured.')

    unfeature_projects.short_description = "Unfeature selected projects"


class CountDisplayMixin:
    """Mixin for displaying count methods"""

    def skills_count(self, obj):
        return obj.skills.count()

    skills_count.short_description = 'Skills Count'

    def projects_count(self, obj):
        return obj.project_set.count()

    projects_count.short_description = 'Projects Count'

    def freelancers_count(self, obj):
        return obj.freelancerprofile_set.count()

    freelancers_count.short_description = 'Freelancers'

    def proposals_count(self, obj):
        return obj.proposal_set.count()

    proposals_count.short_description = 'Proposals Count'
