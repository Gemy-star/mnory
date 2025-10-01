from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.db.models import Q, Avg
from django.core.paginator import Paginator
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from freelancing.forms import ProposalForm, MessageForm, ReviewForm, \
    PaymentForm, FreelancerRegistrationForm, CompanyRegistrationForm
from freelancing.freelancing_utils import create_notification, update_user_rating, complete_project
from freelancing.models import FreelancerProfile, Proposal, Contract, Project, Message, CompanyProfile, Category, Skill, \
    Review, Notification
from shop.models import MnoryUser as User
from django.contrib.auth import login
from shop.user_views import _redirect_by_role


# Dashboard Views
@login_required
def dashboard(request):
    """Main dashboard view that redirects based on user type"""
    if request.user.is_freelancer_user:
        return redirect('freelancer_dashboard')
    elif request.user.is_company_user:
        return redirect('company_dashboard')
    else:
        return redirect('general_dashboard')


@login_required
def freelancer_dashboard(request):
    """Freelancer dashboard with stats and recent activity"""
    if not request.user.is_freelancer_user:
        messages.error(request, "Access denied. Freelancers only.")
        return redirect('dashboard')

    try:
        profile = request.user.freelancer_profile
    except FreelancerProfile.DoesNotExist:
        messages.info(request, "Please complete your freelancer profile first.")
        return redirect('create_freelancer_profile')

    # Get dashboard stats
    active_contracts = Contract.objects.filter(freelancer=request.user, status='active').count()
    pending_proposals = Proposal.objects.filter(freelancer=request.user, status='pending').count()
    total_earnings = profile.total_earnings
    recent_projects = Project.objects.filter(status='open').order_by('-created_at')[:5]
    recent_messages = Message.objects.filter(recipient=request.user, is_read=False)[:5]

    context = {
        'profile': profile,
        'active_contracts': active_contracts,
        'pending_proposals': pending_proposals,
        'total_earnings': total_earnings,
        'recent_projects': recent_projects,
        'recent_messages': recent_messages,
    }
    return render(request, 'freelance/freelancer_dashboard.html', context)


@login_required
def company_dashboard(request):
    """Company dashboard with stats and recent activity"""
    if not request.user.is_company_user:
        messages.error(request, "Access denied. Companies only.")
        return redirect('dashboard')

    try:
        profile = request.user.company_profile
    except CompanyProfile.DoesNotExist:
        messages.info(request, "Please complete your company profile first.")
        return redirect('create_company_profile')

    # Get dashboard stats
    active_projects = Project.objects.filter(client=request.user, status__in=['open', 'in_progress']).count()
    total_proposals = Proposal.objects.filter(project__client=request.user).count()
    total_spent = profile.total_spent
    recent_projects = Project.objects.filter(client=request.user).order_by('-created_at')[:5]
    recent_messages = Message.objects.filter(recipient=request.user, is_read=False)[:5]

    context = {
        'profile': profile,
        'active_projects': active_projects,
        'total_proposals': total_proposals,
        'total_spent': total_spent,
        'recent_projects': recent_projects,
        'recent_messages': recent_messages,
    }
    return render(request, 'freelance/company_dashboard.html', context)


# Project Views
class ProjectListView(ListView):
    model = Project
    template_name = 'freelance/project_list.html'
    context_object_name = 'projects'
    paginate_by = 20

    def get_queryset(self):
        queryset = Project.objects.filter(status='open')

        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(skills_required__name__icontains=search_query)
            ).distinct()

        # Filter by category
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)

        # Filter by project type
        project_type = self.request.GET.get('project_type')
        if project_type:
            queryset = queryset.filter(project_type=project_type)

        # Filter by experience level
        experience_level = self.request.GET.get('experience_level')
        if experience_level:
            queryset = queryset.filter(experience_level=experience_level)

        # Sort options
        sort_by = self.request.GET.get('sort', '-created_at')
        if sort_by in ['-created_at', 'budget_max', '-budget_max', 'proposals_count', '-proposals_count']:
            queryset = queryset.order_by(sort_by)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['current_filters'] = {
            'search': self.request.GET.get('search', ''),
            'category': self.request.GET.get('category', ''),
            'project_type': self.request.GET.get('project_type', ''),
            'experience_level': self.request.GET.get('experience_level', ''),
            'sort': self.request.GET.get('sort', '-created_at'),
        }
        return context


class ProjectDetailView(DetailView):
    model = Project
    template_name = 'freelance/project_detail.html'
    context_object_name = 'project'

    def get_object(self):
        project = super().get_object()
        # Increment view count
        project.views_count += 1
        project.save(update_fields=['views_count'])
        return project

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()

        # Check if current user has already submitted a proposal
        user_proposal = None
        if self.request.user.is_authenticated and self.request.user.is_freelancer_user:
            try:
                user_proposal = Proposal.objects.get(project=project, freelancer=self.request.user)
            except Proposal.DoesNotExist:
                pass

        context['user_proposal'] = user_proposal
        context['proposals'] = project.proposals.filter(status='pending').order_by('-created_at')
        context['similar_projects'] = Project.objects.filter(
            category=project.category,
            status='open'
        ).exclude(id=project.id)[:3]

        return context

@method_decorator(login_required, name='dispatch')
class ProjectUpdateView(UpdateView):
    model = Project
    template_name = 'freelance/project_edit.html'
    fields = [
        'title', 'description', 'category', 'skills_required', 'project_type',
        'budget_min', 'budget_max', 'hourly_rate_min', 'hourly_rate_max',
        'estimated_duration', 'experience_level', 'deadline', 'attachments'
    ]

    def dispatch(self, request, *args, **kwargs):
        project = self.get_object()
        # Only project owner (company user) can edit
        if not request.user.is_company_user or request.user != project.client:
            messages.error(request, "You don't have permission to edit this project.")
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Project updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('project_detail', kwargs={'pk': self.object.pk})


@method_decorator(login_required, name='dispatch')
class ProjectCreateView(CreateView):
    model = Project
    template_name = 'freelance/project_create.html'
    fields = ['title', 'description', 'category', 'skills_required', 'project_type',
              'budget_min', 'budget_max', 'hourly_rate_min', 'hourly_rate_max',
              'estimated_duration', 'experience_level', 'deadline', 'attachments']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_company_user:
            messages.error(request, "Only companies can post projects.")
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.client = self.request.user
        form.instance.status = 'open'
        return super().form_valid(form)

    def get_success_url(self):
        messages.success(self.request, "Project posted successfully!")
        return reverse('project_detail', kwargs={'pk': self.object.pk})


# Proposal Views
@login_required
def submit_proposal(request, project_id):
    """Submit a proposal for a project"""
    if not request.user.is_freelancer_user:
        messages.error(request, "Only freelancers can submit proposals.")
        return redirect('project_detail', pk=project_id)

    project = get_object_or_404(Project, id=project_id, status='open')

    # Check if user already submitted a proposal
    existing_proposal = Proposal.objects.filter(project=project, freelancer=request.user).first()
    if existing_proposal:
        messages.warning(request, "You have already submitted a proposal for this project.")
        return redirect('project_detail', pk=project_id)

    if request.method == 'POST':
        form = ProposalForm(request.POST, request.FILES)
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.project = project
            proposal.freelancer = request.user
            proposal.save()

            # Update project proposal count
            project.proposals_count += 1
            project.save(update_fields=['proposals_count'])

            # Send notification to client
            create_notification(
                user=project.client,
                notification_type='proposal_received',
                title=f"New proposal for {project.title}",
                message=f"You received a new proposal from {request.user.get_full_name() or request.user.email}",
                related_object_id=proposal.id
            )

            messages.success(request, "Your proposal has been submitted successfully!")
            return redirect('project_detail', pk=project_id)
    else:
        form = ProposalForm()

    context = {
        'form': form,
        'project': project,
    }
    return render(request, 'freelance/submit_proposal.html', context)


@login_required
def proposal_detail(request, proposal_id):
    """View proposal details"""
    proposal = get_object_or_404(Proposal, id=proposal_id)

    # Check permissions
    if request.user != proposal.freelancer and request.user != proposal.project.client:
        raise Http404("Proposal not found")

    context = {
        'proposal': proposal,
    }
    return render(request, 'freelance/proposal_detail.html', context)


@login_required
def accept_proposal(request, proposal_id):
    """Accept a proposal and create a contract"""
    proposal = get_object_or_404(Proposal, id=proposal_id)

    # Check permissions
    if request.user != proposal.project.client:
        messages.error(request, "Only the project owner can accept proposals.")
        return redirect('project_detail', pk=proposal.project.id)

    if proposal.status != 'pending':
        messages.error(request, "This proposal has already been processed.")
        return redirect('project_detail', pk=proposal.project.id)

    if request.method == 'POST':
        # Accept the proposal
        proposal.status = 'accepted'
        proposal.save()

        # Reject all other proposals for this project
        Proposal.objects.filter(project=proposal.project).exclude(id=proposal.id).update(status='rejected')

        # Update project status
        proposal.project.status = 'in_progress'
        proposal.project.save()

        # Create contract
        contract = Contract.objects.create(
            project=proposal.project,
            client=proposal.project.client,
            freelancer=proposal.freelancer,
            proposal=proposal,
            title=proposal.project.title,
            description=proposal.project.description,
            amount=proposal.proposed_amount,
            start_date=timezone.now(),
            status='active'
        )

        # Send notifications
        create_notification(
            user=proposal.freelancer,
            notification_type='proposal_accepted',
            title=f"Your proposal was accepted!",
            message=f"Your proposal for '{proposal.project.title}' has been accepted.",
            related_object_id=contract.id
        )

        messages.success(request, "Proposal accepted and contract created!")
        return redirect('contract_detail', pk=contract.id)

    context = {
        'proposal': proposal,
    }
    return render(request, 'freelance/accept_proposal.html', context)


# Freelancer Profile Views
class FreelancerListView(ListView):
    model = FreelancerProfile
    template_name = 'freelance/freelancer_list.html'
    context_object_name = 'freelancers'
    paginate_by = 20

    def get_queryset(self):
        queryset = FreelancerProfile.objects.filter(user__is_active=True)

        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(bio__icontains=search_query) |
                Q(skills__name__icontains=search_query) |
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query)
            ).distinct()

        # Filter by skills
        skill = self.request.GET.get('skill')
        if skill:
            queryset = queryset.filter(skills__name__icontains=skill)

        # Filter by hourly rate
        min_rate = self.request.GET.get('min_rate')
        max_rate = self.request.GET.get('max_rate')
        if min_rate:
            queryset = queryset.filter(hourly_rate__gte=min_rate)
        if max_rate:
            queryset = queryset.filter(hourly_rate__lte=max_rate)

        # Filter by experience level
        experience_level = self.request.GET.get('experience_level')
        if experience_level:
            queryset = queryset.filter(experience_level=experience_level)

        # Sort options
        sort_by = self.request.GET.get('sort', '-rating')
        if sort_by in ['-rating', 'hourly_rate', '-hourly_rate', '-total_jobs_completed']:
            queryset = queryset.order_by(sort_by)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['skills'] = Skill.objects.all()
        context['current_filters'] = {
            'search': self.request.GET.get('search', ''),
            'skill': self.request.GET.get('skill', ''),
            'min_rate': self.request.GET.get('min_rate', ''),
            'max_rate': self.request.GET.get('max_rate', ''),
            'experience_level': self.request.GET.get('experience_level', ''),
            'sort': self.request.GET.get('sort', '-rating'),
        }
        return context


class FreelancerDetailView(DetailView):
    model = FreelancerProfile
    template_name = 'freelance/freelancer_detail.html'
    context_object_name = 'freelancer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        freelancer = self.get_object()

        # Get recent reviews
        context['reviews'] = Review.objects.filter(reviewee=freelancer.user, is_public=True).order_by('-created_at')[
            :10]

        # Get completed projects count
        context['completed_projects'] = Contract.objects.filter(freelancer=freelancer.user, status='completed').count()

        # Calculate average rating
        avg_rating = Review.objects.filter(reviewee=freelancer.user).aggregate(Avg('rating'))['rating__avg']
        context['avg_rating'] = round(avg_rating, 1) if avg_rating else 0

        return context


# Company Profile Views
class CompanyListView(ListView):
    model = CompanyProfile
    template_name = 'freelance/company_list.html'
    context_object_name = 'companies'
    paginate_by = 20

    def get_queryset(self):
        queryset = CompanyProfile.objects.filter(user__is_active=True)

        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(company_name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(industry__icontains=search_query) |
                Q(location__icontains=search_query)
            ).distinct()

        # Filter by industry
        industry = self.request.GET.get('industry')
        if industry:
            queryset = queryset.filter(industry__icontains=industry)

        # Filter by company size
        company_size = self.request.GET.get('company_size')
        if company_size:
            queryset = queryset.filter(company_size=company_size)

        # Sort options
        sort_by = self.request.GET.get('sort', '-rating')
        if sort_by in ['-rating', '-total_jobs_posted', '-total_spent', 'company_name']:
            queryset = queryset.order_by(sort_by)

        return queryset


class CompanyDetailView(DetailView):
    model = CompanyProfile
    template_name = 'freelance/company_detail.html'
    context_object_name = 'company'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.get_object()

        # Get recent projects
        context['recent_projects'] = Project.objects.filter(client=company.user, status='open').order_by('-created_at')[
            :5]

        # Get reviews from freelancers
        context['reviews'] = Review.objects.filter(reviewee=company.user, is_public=True).order_by('-created_at')[:10]

        # Calculate average rating
        avg_rating = Review.objects.filter(reviewee=company.user).aggregate(Avg('rating'))['rating__avg']
        context['avg_rating'] = round(avg_rating, 1) if avg_rating else 0

        return context


# Contract Views
@login_required
def contract_list(request):
    """List all contracts for the current user"""
    if request.user.is_freelancer_user:
        contracts = Contract.objects.filter(freelancer=request.user)
    elif request.user.is_company_user:
        contracts = Contract.objects.filter(client=request.user)
    else:
        contracts = Contract.objects.none()

    # Filter by status
    status = request.GET.get('status')
    if status:
        contracts = contracts.filter(status=status)

    contracts = contracts.order_by('-created_at')

    # Pagination
    paginator = Paginator(contracts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'contracts': page_obj,
        'current_status': status,
    }
    return render(request, 'freelance/contract_list.html', context)


class ContractDetailView(LoginRequiredMixin, DetailView):
    model = Contract
    template_name = 'freelance/contract_detail.html'
    context_object_name = 'contract'

    def get_object(self):
        contract = super().get_object()
        # Check permissions
        if self.request.user != contract.client and self.request.user != contract.freelancer:
            raise Http404("Contract not found")
        return contract

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contract = self.get_object()

        # Get payments
        context['payments'] = contract.payments.all().order_by('-created_at')

        # Get messages related to this contract
        context['messages'] = Message.objects.filter(contract=contract).order_by('created_at')

        # Get reviews
        context['reviews'] = contract.reviews.all()

        # Check if current user can leave a review
        user_review = contract.reviews.filter(reviewer=self.request.user).first()
        context['user_review'] = user_review
        context['can_review'] = contract.status == 'completed' and not user_review

        return context


# Message Views
@login_required
def message_list(request):
    """List all messages for the current user"""
    messages_received = Message.objects.filter(recipient=request.user).order_by('-created_at')
    messages_sent = Message.objects.filter(sender=request.user).order_by('-created_at')

    # Mark messages as read when viewed
    messages_received.filter(is_read=False).update(is_read=True)

    context = {
        'messages_received': messages_received[:20],
        'messages_sent': messages_sent[:20],
        'unread_count': messages_received.filter(is_read=False).count(),
    }
    return render(request, 'freelance/message_list.html', context)


@login_required
def send_message(request, user_id=None, project_id=None, contract_id=None):
    """Send a message to another user."""

    def get_recipient():
        """Resolve recipient based on given parameters."""
        if user_id:
            return get_object_or_404(User, id=user_id), None, None
        if project_id:
            project = get_object_or_404(Project, id=project_id)
            recipient = project.client if request.user != project.client else None
            return recipient, project, None
        if contract_id:
            contract = get_object_or_404(Contract, id=contract_id)
            if request.user not in [contract.client, contract.freelancer]:
                return None, None, None
            recipient = contract.freelancer if request.user == contract.client else contract.client
            return recipient, None, contract
        return None, None, None

    recipient, project, contract = get_recipient()

    if not recipient:
        messages.error(request, "Recipient not specified or permission denied.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.recipient = recipient
            message.project = project
            message.contract = contract
            message.save()

            # Send notification
            preview = (message.message[:100] + '...') if len(message.message) > 100 else message.message
            create_notification(
                user=recipient,
                notification_type='message_received',
                title=f"New message from {request.user.get_full_name() or request.user.email}",
                message=preview,
                related_object_id=message.id
            )

            messages.success(request, "Message sent successfully!")
            return redirect('message_list')
    else:
        initial_data = {}
        if project:
            initial_data['subject'] = f"Regarding: {project.title}"
        elif contract:
            initial_data['subject'] = f"Regarding Contract: {contract.title}"
        form = MessageForm(initial=initial_data)

    return render(request, 'freelance/send_message.html', {
        'form': form,
        'recipient': recipient,
        'project': project,
        'contract': contract,
    })



# Review Views
@login_required
def submit_review(request, contract_id):
    """Submit a review for a completed contract"""
    contract = get_object_or_404(Contract, id=contract_id, status='completed')

    # Check permissions
    if request.user not in [contract.client, contract.freelancer]:
        messages.error(request, "You don't have permission to review this contract.")
        return redirect('contract_detail', pk=contract_id)

    # Check if user already reviewed
    existing_review = Review.objects.filter(contract=contract, reviewer=request.user).first()
    if existing_review:
        messages.warning(request, "You have already reviewed this contract.")
        return redirect('contract_detail', pk=contract_id)

    # Determine who is being reviewed
    reviewee = contract.freelancer if request.user == contract.client else contract.client

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.contract = contract
            review.reviewer = request.user
            review.reviewee = reviewee
            review.save()

            # Update user's rating
            update_user_rating(reviewee)

            # Send notification
            create_notification(
                user=reviewee,
                notification_type='review_received',
                title=f"New review received",
                message=f"You received a {review.rating}-star review for '{contract.title}'",
                related_object_id=review.id
            )

            messages.success(request, "Review submitted successfully!")
            return redirect('contract_detail', pk=contract_id)
    else:
        form = ReviewForm()

    context = {
        'form': form,
        'contract': contract,
        'reviewee': reviewee,
    }
    return render(request, 'freelance/submit_review.html', context)

def register_company(request):
    """Register a new company user + profile"""
    if request.method == 'POST':
        form = CompanyRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, _("Company account created successfully."))
            login(request, user)  # ✅ auto login
            return _redirect_by_role(user)  # ✅ redirect based on role
    else:
        form = CompanyRegistrationForm()

    return render(request, 'freelance/create_company_profile.html', {
        'form': form,
        'title': _("Company Registration"),
        'form_action': request.path,
        'submit_label': _("Register as Company"),
    })


def register_freelancer(request):
    """Register a new freelancer user + profile"""
    if request.method == 'POST':
        form = FreelancerRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, _("Freelancer account created successfully."))
            login(request, user)  # ✅ auto login
            return _redirect_by_role(user)  # ✅ redirect based on role
    else:
        form = FreelancerRegistrationForm()

    return render(request, 'freelance/create_freelancer_profile.html', {
        'form': form,
        'title': _("Freelancer Registration"),
        'form_action': request.path,
        'submit_label': _("Register as Freelancer"),
    })


@login_required
def edit_freelancer_profile(request):
    """Edit existing freelancer profile"""
    if not request.user.user_type == 'freelancer':
        messages.error(request, "Only freelancer accounts can edit a freelancer profile.")
        return redirect('dashboard')

    profile = get_object_or_404(FreelancerProfile, user=request.user)

    if request.method == 'POST':
        form = FreelancerRegistrationForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Freelancer profile updated successfully!")
            return redirect('freelancer_dashboard')
    else:
        form = FreelancerRegistrationForm(instance=profile)

    return render(request, 'freelance/edit_freelancer_profile.html', {
        'form': form,
        'profile': profile,
    })


@login_required
def edit_company_profile(request):
    """Edit existing company profile"""
    if not request.user.user_type == 'company':
        messages.error(request, "Only company accounts can edit a company profile.")
        return redirect('dashboard')

    profile = get_object_or_404(CompanyProfile, user=request.user)

    if request.method == 'POST':
        form = CompanyRegistrationForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Company profile updated successfully!")
            return redirect('company_dashboard')
    else:
        form = CompanyRegistrationForm(instance=profile)

    return render(request, 'freelance/edit_company_profile.html', {
        'form': form,
        'profile': profile,
    })

# API Views for AJAX requests
@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    if request.method == 'POST':
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})


@login_required
def get_notifications(request):
    """Get unread notifications for current user"""
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:10]
    data = [{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'created_at': n.created_at.strftime('%Y-%m-%d %H:%M'),
        'type': n.notification_type
    } for n in notifications]
    return JsonResponse({'notifications': data})


# Search and Filter Views
def search_projects(request):
    """AJAX search for projects"""
    query = request.GET.get('q', '')
    projects = Project.objects.filter(
        Q(title__icontains=query) | Q(description__icontains=query),
        status='open'
    )[:10]

    data = [{
        'id': str(p.id),
        'title': p.title,
        'budget': str(p.budget_max) if p.budget_max else 'N/A',
        'client': p.client.get_full_name() or p.client.email,
        'created_at': p.created_at.strftime('%Y-%m-%d')
    } for p in projects]

    return JsonResponse({'projects': data})


def search_freelancers(request):
    """AJAX search for freelancers"""
    query = request.GET.get('q', '')
    freelancers = FreelancerProfile.objects.filter(
        Q(title__icontains=query) | Q(bio__icontains=query) | Q(skills__name__icontains=query),
        user__is_active=True
    ).distinct()[:10]

    data = [{
        'id': f.id,
        'name': f.user.get_full_name() or f.user.email,
        'title': f.title,
        'hourly_rate': str(f.hourly_rate),
        'rating': str(f.rating),
        'location': f.location
    } for f in freelancers]

    return JsonResponse({'freelancers': data})

def complete_contract(request, contract_id):
    """Mark contract as completed"""
    contract = get_object_or_404(Contract, id=contract_id)

    # Check permissions
    if request.user not in [contract.client, contract.freelancer]:
        messages.error(request, "You don't have permission to complete this contract.")
        return redirect('contract_detail', pk=contract_id)

    if request.method == 'POST':
        complete_project(contract)
        messages.success(request, "Contract marked as completed!")
        return redirect('contract_detail', pk=contract_id)

    context = {'contract': contract}
    return render(request, 'freelance/complete_contract.html', context)


def create_payment(request, contract_id):
    """Create a milestone payment"""
    contract = get_object_or_404(Contract, id=contract_id)

    # Check permissions (only client can create payments)
    if request.user != contract.client:
        messages.error(request, "Only the client can create payments.")
        return redirect('contract_detail', pk=contract_id)

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.contract = contract
            payment.save()

            messages.success(request, "Payment milestone created successfully!")
            return redirect('contract_detail', pk=contract_id)
    else:
        form = PaymentForm()

    context = {
        'form': form,
        'contract': contract,
    }
    return render(request, 'freelance/create_payment.html', context)

