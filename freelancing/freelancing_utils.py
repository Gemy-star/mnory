from django.db.models import Avg, Count, Sum
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from .models import *
import uuid
from decimal import Decimal
from datetime import datetime, timedelta

User = get_user_model()


def create_notification(user, notification_type, title, message, related_object_id=None):
    """Create a notification for a user"""
    return Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        related_object_id=related_object_id
    )


def update_user_rating(user):
    """Update user's average rating based on reviews"""
    reviews = Review.objects.filter(reviewee=user)
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']

    if user.is_freelancer_user and hasattr(user, 'freelancer_profile'):
        user.freelancer_profile.rating = avg_rating or 0
        user.freelancer_profile.save(update_fields=['rating'])
    elif user.is_company_user and hasattr(user, 'company_profile'):
        user.company_profile.rating = avg_rating or 0
        user.company_profile.save(update_fields=['rating'])


def calculate_platform_fee(amount, user_type='freelancer'):
    """Calculate platform fee based on amount and user type"""
    fee_percentage = getattr(settings, 'PLATFORM_FEE_PERCENTAGE', 0.05)  # 5% default

    if user_type == 'freelancer':
        # Tiered fee structure for freelancers
        if amount <= 500:
            fee_percentage = 0.20  # 20% for first $500
        elif amount <= 10000:
            fee_percentage = 0.10  # 10% for $500.01 to $10,000
        else:
            fee_percentage = 0.05  # 5% for amounts over $10,000
    else:
        fee_percentage = 0.03  # 3% for clients

    return amount * Decimal(str(fee_percentage))


def process_payment(contract, amount, payment_type='milestone', description=''):
    """Process a payment for a contract"""
    # Calculate platform fee
    platform_fee = calculate_platform_fee(amount, 'freelancer')
    freelancer_amount = amount - platform_fee

    # Create payment record
    payment = Payment.objects.create(
        contract=contract,
        amount=amount,
        payment_type=payment_type,
        description=description,
        status='completed',
        paid_date=timezone.now(),
        transaction_id=str(uuid.uuid4())
    )

    # Update freelancer earnings
    if hasattr(contract.freelancer, 'freelancer_profile'):
        profile = contract.freelancer.freelancer_profile
        profile.total_earnings += freelancer_amount
        profile.save(update_fields=['total_earnings'])

    # Update company spending
    if hasattr(contract.client, 'company_profile'):
        profile = contract.client.company_profile
        profile.total_spent += amount
        profile.save(update_fields=['total_spent'])

    # Send notifications
    create_notification(
        user=contract.freelancer,
        notification_type='payment_received',
        title=f"Payment received: ${freelancer_amount}",
        message=f"You received ${freelancer_amount} for '{contract.title}'",
        related_object_id=payment.id
    )

    return payment


def complete_project(contract):
    """Complete a project and update related statistics"""
    contract.status = 'completed'
    contract.end_date = timezone.now()
    contract.save()

    # Update project status
    contract.project.status = 'completed'
    contract.project.save()

    # Update freelancer job count
    if hasattr(contract.freelancer, 'freelancer_profile'):
        profile = contract.freelancer.freelancer_profile
        profile.total_jobs_completed += 1
        profile.save(update_fields=['total_jobs_completed'])

    # Update company job count
    if hasattr(contract.client, 'company_profile'):
        profile = contract.client.company_profile
        profile.total_jobs_posted += 1
        profile.save(update_fields=['total_jobs_posted'])

    # Send notifications
    create_notification(
        user=contract.client,
        notification_type='project_completed',
        title=f"Project completed: {contract.title}",
        message=f"Your project '{contract.title}' has been completed by {contract.freelancer.get_full_name()}",
        related_object_id=contract.id
    )

    create_notification(
        user=contract.freelancer,
        notification_type='project_completed',
        title=f"Project completed: {contract.title}",
        message=f"You have successfully completed '{contract.title}'",
        related_object_id=contract.id
    )


def send_email_notification(user, subject, message, html_message=None):
    """Send email notification to user"""
    if user.email:
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False
            )
            return True
        except Exception as e:
            print(f"Email sending failed: {e}")
            return False
    return False


def get_recommended_freelancers(project, limit=10):
    """Get recommended freelancers for a project based on skills and rating"""
    required_skills = project.skills_required.all()

    # Find freelancers with matching skills
    freelancers = FreelancerProfile.objects.filter(
        skills__in=required_skills,
        user__is_active=True,
        experience_level__in=[project.experience_level, 'expert']  # Include higher levels
    ).annotate(
        skill_matches=Count('skills', filter=models.Q(skills__in=required_skills))
    ).filter(
        skill_matches__gt=0
    ).order_by('-rating', '-skill_matches', '-total_jobs_completed')[:limit]

    return freelancers


def get_recommended_projects(freelancer_user, limit=10):
    """Get recommended projects for a freelancer based on skills"""
    if not hasattr(freelancer_user, 'freelancer_profile'):
        return Project.objects.none()

    profile = freelancer_user.freelancer_profile
    user_skills = profile.skills.all()

    # Find projects with matching skills
    projects = Project.objects.filter(
        status='open',
        skills_required__in=user_skills,
        experience_level__in=['entry', profile.experience_level]  # Include lower levels
    ).annotate(
        skill_matches=Count('skills_required', filter=models.Q(skills_required__in=user_skills))
    ).filter(
        skill_matches__gt=0
    ).exclude(
        proposals__freelancer=freelancer_user  # Exclude already applied projects
    ).order_by('-skill_matches', '-created_at')[:limit]

    return projects


def calculate_project_budget_range(category, experience_level='intermediate'):
    """Calculate suggested budget range for a project based on category and experience"""
    base_rates = {
        'entry': {'min': 10, 'max': 25},
        'intermediate': {'min': 25, 'max': 50},
        'expert': {'min': 50, 'max': 100}
    }

    # Get average rates for the category (simplified)
    rates = base_rates.get(experience_level, base_rates['intermediate'])

    # Estimate project duration (hours)
    estimated_hours = 40  # Default 40 hours

    return {
        'min_budget': rates['min'] * estimated_hours,
        'max_budget': rates['max'] * estimated_hours,
        'suggested_hourly_min': rates['min'],
        'suggested_hourly_max': rates['max']
    }


def get_user_dashboard_stats(user):
    """Get dashboard statistics for a user"""
    stats = {}

    if user.is_freelancer_user and hasattr(user, 'freelancer_profile'):
        profile = user.freelancer_profile
        stats = {
            'active_contracts': Contract.objects.filter(freelancer=user, status='active').count(),
            'pending_proposals': Proposal.objects.filter(freelancer=user, status='pending').count(),
            'completed_jobs': profile.total_jobs_completed,
            'total_earnings': profile.total_earnings,
            'avg_rating': profile.rating,
            'profile_views': 0,  # You can implement view tracking
        }
    elif user.is_company_user and hasattr(user, 'company_profile'):
        profile = user.company_profile
        stats = {
            'active_projects': Project.objects.filter(client=user, status__in=['open', 'in_progress']).count(),
            'total_projects': Project.objects.filter(client=user).count(),
            'total_spent': profile.total_spent,
            'avg_rating': profile.rating,
            'total_proposals_received': Proposal.objects.filter(project__client=user).count(),
        }

    # Common stats for all users
    stats.update({
        'unread_messages': Message.objects.filter(recipient=user, is_read=False).count(),
        'unread_notifications': Notification.objects.filter(user=user, is_read=False).count(),
    })

    return stats


def search_and_filter_projects(request):
    """Advanced search and filtering for projects"""
    queryset = Project.objects.filter(status='open')

    # Search query
    search = request.GET.get('search', '').strip()
    if search:
        queryset = queryset.filter(
            models.Q(title__icontains=search) |
            models.Q(description__icontains=search) |
            models.Q(skills_required__name__icontains=search)
        ).distinct()

    # Category filter
    category_slug = request.GET.get('category')
    if category_slug:
        queryset = queryset.filter(category__slug=category_slug)

    # Budget range filter
    min_budget = request.GET.get('min_budget')
    max_budget = request.GET.get('max_budget')
    if min_budget:
        queryset = queryset.filter(
            models.Q(budget_min__gte=min_budget) |
            models.Q(budget_max__gte=min_budget)
        )
    if max_budget:
        queryset = queryset.filter(
            models.Q(budget_max__lte=max_budget) |
            models.Q(budget_min__lte=max_budget)
        )

    # Experience level filter
    experience_level = request.GET.get('experience_level')
    if experience_level:
        queryset = queryset.filter(experience_level=experience_level)

    # Project type filter
    project_type = request.GET.get('project_type')
    if project_type:
        queryset = queryset.filter(project_type=project_type)

    # Skills filter
    skills = request.GET.getlist('skills')
    if skills:
        queryset = queryset.filter(skills_required__id__in=skills).distinct()

    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    valid_sorts = ['-created_at', 'created_at', '-budget_max', 'budget_max',
                   '-proposals_count', 'proposals_count', 'deadline', '-deadline']
    if sort_by in valid_sorts:
        queryset = queryset.order_by(sort_by)

    return queryset


def search_and_filter_freelancers(request):
    """Advanced search and filtering for freelancers"""
    queryset = FreelancerProfile.objects.filter(user__is_active=True)

    # Search query
    search = request.GET.get('search', '').strip()
    if search:
        queryset = queryset.filter(
            models.Q(title__icontains=search) |
            models.Q(bio__icontains=search) |
            models.Q(skills__name__icontains=search) |
            models.Q(user__first_name__icontains=search) |
            models.Q(user__last_name__icontains=search)
        ).distinct()

    # Hourly rate range
    min_rate = request.GET.get('min_rate')
    max_rate = request.GET.get('max_rate')
    if min_rate:
        queryset = queryset.filter(hourly_rate__gte=min_rate)
    if max_rate:
        queryset = queryset.filter(hourly_rate__lte=max_rate)

    # Experience level filter
    experience_level = request.GET.get('experience_level')
    if experience_level:
        queryset = queryset.filter(experience_level=experience_level)

    # Skills filter
    skills = request.GET.getlist('skills')
    if skills:
        queryset = queryset.filter(skills__id__in=skills).distinct()

    # Location filter
    location = request.GET.get('location')
    if location:
        queryset = queryset.filter(location__icontains=location)

    # Availability filter
    availability = request.GET.get('availability')
    if availability:
        queryset = queryset.filter(availability=availability)

    # Rating filter
    min_rating = request.GET.get('min_rating')
    if min_rating:
        queryset = queryset.filter(rating__gte=min_rating)

    # Verified filter
    verified_only = request.GET.get('verified')
    if verified_only == 'true':
        queryset = queryset.filter(is_verified=True)

    # Sorting
    sort_by = request.GET.get('sort', '-rating')
    valid_sorts = ['-rating', 'rating', '-hourly_rate', 'hourly_rate',
                   '-total_jobs_completed', 'total_jobs_completed', '-created_at', 'created_at']
    if sort_by in valid_sorts:
        queryset = queryset.order_by(sort_by)

    return queryset


def validate_project_data(project_data):
    """Validate project data before creation"""
    errors = []

    # Check required fields
    required_fields = ['title', 'description', 'category', 'project_type', 'experience_level']
    for field in required_fields:
        if not project_data.get(field):
            errors.append(f"{field.replace('_', ' ').title()} is required")

    # Validate budget based on project type
    if project_data.get('project_type') == 'fixed':
        if not project_data.get('budget_min') or not project_data.get('budget_max'):
            errors.append("Budget range is required for fixed price projects")
        elif project_data.get('budget_min', 0) > project_data.get('budget_max', 0):
            errors.append("Minimum budget cannot be greater than maximum budget")
    elif project_data.get('project_type') == 'hourly':
        if not project_data.get('hourly_rate_min') or not project_data.get('hourly_rate_max'):
            errors.append("Hourly rate range is required for hourly projects")
        elif project_data.get('hourly_rate_min', 0) > project_data.get('hourly_rate_max', 0):
            errors.append("Minimum hourly rate cannot be greater than maximum hourly rate")

    return errors


def calculate_proposal_success_rate(freelancer_user):
    """Calculate proposal success rate for a freelancer"""
    total_proposals = Proposal.objects.filter(freelancer=freelancer_user).count()
    if total_proposals == 0:
        return 0

    accepted_proposals = Proposal.objects.filter(freelancer=freelancer_user, status='accepted').count()
    return round((accepted_proposals / total_proposals) * 100, 2)


def get_trending_skills():
    """Get trending skills based on recent project requirements"""
    from django.db.models import Count
    from datetime import timedelta

    last_30_days = timezone.now() - timedelta(days=30)
    trending_skills = Skill.objects.filter(
        project__created_at__gte=last_30_days,
        project__status='open'
    ).annotate(
        demand_count=Count('project')
    ).order_by('-demand_count')[:20]

    return trending_skills


def send_proposal_notifications(proposal):
    """Send notifications when a new proposal is submitted"""
    # Notify the project owner
    create_notification(
        user=proposal.project.client,
        notification_type='proposal_received',
        title=f"New proposal for '{proposal.project.title}'",
        message=f"You received a proposal from {proposal.freelancer.get_full_name() or proposal.freelancer.email}",
        related_object_id=proposal.id
    )

    # Send email notification
    subject = f"New Proposal Received - {proposal.project.title}"
    message = f"""
    Hi {proposal.project.client.get_full_name() or proposal.project.client.email},

    You have received a new proposal for your project "{proposal.project.title}".

    Freelancer: {proposal.freelancer.get_full_name() or proposal.freelancer.email}
    Proposed Amount: ${proposal.proposed_amount}
    Estimated Duration: {proposal.estimated_duration}

    Please log in to review the proposal.

    Best regards,
    Your Freelance Platform Team
    """

    send_email_notification(proposal.project.client, subject, message)


def auto_complete_contract_milestones(contract):
    """Auto-complete contract based on milestones or time"""
    # This is a simplified version - in reality, you'd have more complex logic
    if contract.status == 'active':
        # Check if all milestones are completed
        total_payments = contract.payments.filter(status='completed').aggregate(
            total=Sum('amount')
        )['total'] or 0

        if total_payments >= contract.amount:
            complete_project(contract)
            return True

    return False


def generate_contract_terms(project, proposal):
    """Generate standard contract terms and conditions"""
    terms = f"""
    CONTRACT TERMS AND CONDITIONS

    Project: {project.title}
    Client: {project.client.get_full_name() or project.client.email}
    Freelancer: {proposal.freelancer.get_full_name() or proposal.freelancer.email}

    1. SCOPE OF WORK
    {project.description}

    2. PAYMENT TERMS
    Total Amount: ${proposal.proposed_amount}
    Payment Schedule: As agreed upon completion of milestones

    3. TIMELINE
    Estimated Duration: {proposal.estimated_duration}
    Start Date: {timezone.now().strftime('%Y-%m-%d')}

    4. DELIVERABLES
    All work products shall be delivered as specified in the project description.

    5. INTELLECTUAL PROPERTY
    Upon full payment, all intellectual property rights shall transfer to the client.

    6. TERMINATION
    Either party may terminate this contract with 7 days written notice.

    7. PLATFORM FEES
    Platform fees will be deducted as per platform policy.

    By accepting this contract, both parties agree to these terms and conditions.
    """

    return terms


def calculate_estimated_earnings(hourly_rate, hours_per_week, weeks):
    """Calculate estimated earnings for freelancers"""
    gross_earnings = hourly_rate * hours_per_week * weeks
    platform_fee = calculate_platform_fee(gross_earnings, 'freelancer')
    net_earnings = gross_earnings - platform_fee

    return {
        'gross_earnings': gross_earnings,
        'platform_fee': platform_fee,
        'net_earnings': net_earnings,
        'effective_hourly_rate': net_earnings / (hours_per_week * weeks)
    }


def get_market_rate_insights(category, experience_level):
    """Get market rate insights for a category and experience level"""
    freelancers = FreelancerProfile.objects.filter(
        skills__category=category,
        experience_level=experience_level,
        user__is_active=True
    )

    if not freelancers.exists():
        return None

    rates = freelancers.values_list('hourly_rate', flat=True)

    return {
        'min_rate': min(rates),
        'max_rate': max(rates),
        'avg_rate': sum(rates) / len(rates),
        'median_rate': sorted(rates)[len(rates) // 2],
        'sample_size': len(rates)
    }


def cleanup_expired_proposals():
    """Cleanup expired proposals (run as periodic task)"""
    expired_date = timezone.now() - timedelta(days=30)
    expired_proposals = Proposal.objects.filter(
        created_at__lt=expired_date,
        status='pending',
        project__status__in=['cancelled', 'completed']
    )

    expired_count = expired_proposals.count()
    expired_proposals.update(status='withdrawn')

    return expired_count


def generate_invoice_data(payment):
    """Generate invoice data for a payment"""
    platform_fee = calculate_platform_fee(payment.amount, 'freelancer')
    net_amount = payment.amount - platform_fee

    return {
        'invoice_number': f"INV-{payment.id}",
        'date': payment.created_at.strftime('%Y-%m-%d'),
        'client_name': payment.contract.client.get_full_name() or payment.contract.client.email,
        'freelancer_name': payment.contract.freelancer.get_full_name() or payment.contract.freelancer.email,
        'project_title': payment.contract.title,
        'gross_amount': payment.amount,
        'platform_fee': platform_fee,
        'net_amount': net_amount,
        'payment_date': payment.paid_date.strftime('%Y-%m-%d') if payment.paid_date else None,
    }


def check_user_verification_status(user):
    """Check if user meets verification criteria"""
    criteria = {
        'email_verified': True,  # Assume email is verified during registration
        'phone_verified': bool(user.phone_number),
        'profile_complete': False,
        'has_reviews': False,
        'identity_verified': False,  # This would require additional implementation
    }

    if user.is_freelancer_user and hasattr(user, 'freelancer_profile'):
        profile = user.freelancer_profile
        criteria['profile_complete'] = bool(
            profile.title and profile.bio and profile.hourly_rate and
            profile.skills.exists() and profile.profile_picture
        )
        criteria['has_reviews'] = Review.objects.filter(reviewee=user).exists()
    elif user.is_company_user and hasattr(user, 'company_profile'):
        profile = user.company_profile
        criteria['profile_complete'] = bool(
            profile.company_name and profile.description and
            profile.industry and profile.location
        )
        criteria['has_reviews'] = Review.objects.filter(reviewee=user).exists()

    verification_score = sum(criteria.values()) / len(criteria) * 100

    return {
        'criteria': criteria,
        'score': round(verification_score, 2),
        'is_verifiable': verification_score >= 80
    }


def get_user_activity_timeline(user, limit=50):
    """Get user activity timeline"""
    activities = []

    # Get proposals
    proposals = Proposal.objects.filter(freelancer=user).order_by('-created_at')[:limit // 4]
    for proposal in proposals:
        activities.append({
            'type': 'proposal_submitted',
            'title': f"Submitted proposal for '{proposal.project.title}'",
            'date': proposal.created_at,
            'url': reverse('proposal_detail', kwargs={'proposal_id': proposal.id}),
        })

    # Get contracts
    contracts = Contract.objects.filter(
        models.Q(freelancer=user) | models.Q(client=user)
    ).order_by('-created_at')[:limit // 4]

    for contract in contracts:
        role = 'freelancer' if contract.freelancer == user else 'client'
        activities.append({
            'type': f'contract_created_{role}',
            'title': f"Contract created for '{contract.title}'",
            'date': contract.created_at,
            'url': reverse('contract_detail', kwargs={'pk': contract.pk}),
        })

    # Get reviews
    reviews = Review.objects.filter(
        models.Q(reviewer=user) | models.Q(reviewee=user)
    ).order_by('-created_at')[:limit // 4]

    for review in reviews:
        role = 'gave' if review.reviewer == user else 'received'
        activities.append({
            'type': f'review_{role}',
            'title': f"{'Gave' if role == 'gave' else 'Received'} {review.rating}-star review",
            'date': review.created_at,
            'url': reverse('contract_detail', kwargs={'pk': review.contract.pk}),
        })

    # Get projects (for companies)
    if user.is_company_user:
        projects = Project.objects.filter(client=user).order_by('-created_at')[:limit // 4]
        for project in projects:
            activities.append({
                'type': 'project_posted',
                'title': f"Posted project '{project.title}'",
                'date': project.created_at,
                'url': reverse('project_detail', kwargs={'pk': project.pk}),
            })

    # Sort all activities by date
    activities.sort(key=lambda x: x['date'], reverse=True)

    return activities[:limit]
