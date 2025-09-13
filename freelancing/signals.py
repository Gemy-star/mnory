# -------------------------------
# Freelance Platform Email Signals
# Add this to your freelance/signals.py file or create a new one
# -------------------------------

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
import logging

from shop.email import send_email_with_sendgrid
# Import your freelance models
from freelancing.models import (
    FreelancerProfile, CompanyProfile, Project, Proposal,
    Contract, Payment, Review, Message, Notification
)

# Import the email functions we created
from freelancing.utils import (
    # Freelancer emails
    send_freelancer_registration_email,
    send_freelancer_verification_email,

    # Company emails
    send_company_registration_email,
    send_company_verification_email,

    # Project emails
    send_project_posted_email,
    send_project_status_update_email,

    # Proposal emails
    send_proposal_submitted_email,
    send_proposal_received_email,
    send_proposal_status_update_email,

    # Contract emails
    send_contract_created_email,
    send_contract_status_update_email,

    # Payment emails
    send_payment_completed_email,
    send_payment_due_reminder_email,

    # Review emails
    send_review_received_email,

    # Message emails
    send_message_notification_email,

    # Admin notification emails
    send_admin_new_freelancer_notification,
    send_admin_new_company_notification,
    send_admin_new_project_notification,
    send_admin_contract_created_notification,
)

logger = logging.getLogger(__name__)


# -------------------------------
# Freelancer Profile Signals
# -------------------------------

@receiver(post_save, sender=FreelancerProfile)
def handle_freelancer_profile_created(sender, instance, created, **kwargs):
    """
    Send freelancer registration email when a freelancer profile is created
    """
    if created:
        logger.info(f"New freelancer profile created: {instance.user.email}")

        try:
            # Send registration email to freelancer
            send_freelancer_registration_email(instance.user, instance)

            # Send admin notification
            send_admin_new_freelancer_notification(instance.user, instance)
        except Exception as e:
            logger.error(f"Failed to send freelancer registration emails for {instance.user.email}: {str(e)}")


@receiver(pre_save, sender=FreelancerProfile)
def handle_freelancer_verification_change(sender, instance, **kwargs):
    """
    Send verification email when freelancer verification status changes
    """
    if instance.pk:  # Only for existing freelancer profiles
        try:
            old_instance = FreelancerProfile.objects.get(pk=instance.pk)
            old_verification_status = old_instance.is_verified
            new_verification_status = instance.is_verified

            # Check if verification status changed to True
            if not old_verification_status and new_verification_status:
                logger.info(f"Freelancer {instance.user.email} verified")

                from django.db import transaction
                transaction.on_commit(
                    lambda: send_freelancer_verification_email(instance.user, instance)
                )

        except FreelancerProfile.DoesNotExist:
            logger.warning(
                f"Could not find existing freelancer profile {instance.pk} for verification change comparison")
        except Exception as e:
            logger.error(f"Error handling freelancer verification change for {instance.user.email}: {str(e)}")


# -------------------------------
# Company Profile Signals
# -------------------------------

@receiver(post_save, sender=CompanyProfile)
def handle_company_profile_created(sender, instance, created, **kwargs):
    """
    Send company registration email when a company profile is created
    """
    if created:
        logger.info(f"New company profile created: {instance.company_name}")

        try:
            # Send registration email to company
            send_company_registration_email(instance.user, instance)

            # Send admin notification
            send_admin_new_company_notification(instance.user, instance)
        except Exception as e:
            logger.error(f"Failed to send company registration emails for {instance.user.email}: {str(e)}")


@receiver(pre_save, sender=CompanyProfile)
def handle_company_verification_change(sender, instance, **kwargs):
    """
    Send verification email when company verification status changes
    """
    if instance.pk:  # Only for existing company profiles
        try:
            old_instance = CompanyProfile.objects.get(pk=instance.pk)
            old_verification_status = old_instance.is_verified
            new_verification_status = instance.is_verified

            # Check if verification status changed to True
            if not old_verification_status and new_verification_status:
                logger.info(f"Company {instance.company_name} verified")

                from django.db import transaction
                transaction.on_commit(
                    lambda: send_company_verification_email(instance.user, instance)
                )

        except CompanyProfile.DoesNotExist:
            logger.warning(f"Could not find existing company profile {instance.pk} for verification change comparison")
        except Exception as e:
            logger.error(f"Error handling company verification change for {instance.user.email}: {str(e)}")


# -------------------------------
# Project Related Signals
# -------------------------------

@receiver(post_save, sender=Project)
def handle_project_created(sender, instance, created, **kwargs):
    """
    Send project posted email when a new project is created and published
    """
    if created and instance.status == 'open':  # Only send for published projects
        logger.info(f"New project posted: {instance.title}")

        try:
            # Send project posted confirmation email to client
            send_project_posted_email(instance)

            # Send admin notification
            send_admin_new_project_notification(instance)
        except Exception as e:
            logger.error(f"Failed to send project posted emails for {instance.title}: {str(e)}")


@receiver(pre_save, sender=Project)
def handle_project_status_change(sender, instance, **kwargs):
    """
    Send project status update email when project status changes
    """
    if instance.pk:  # Only for existing projects
        try:
            old_instance = Project.objects.get(pk=instance.pk)
            old_status = old_instance.status
            new_status = instance.status

            # Check if status actually changed
            if old_status != new_status:
                logger.info(f"Project {instance.title} status changed from {old_status} to {new_status}")

                # Send status update email after the save completes
                from django.db import transaction
                transaction.on_commit(
                    lambda: send_project_status_update_email(instance, old_status, new_status)
                )
        except Project.DoesNotExist:
            logger.warning(f"Could not find existing project {instance.pk} for status change comparison")
        except Exception as e:
            logger.error(f"Error handling project status change for {instance.title}: {str(e)}")


# -------------------------------
# Proposal Related Signals
# -------------------------------

@receiver(post_save, sender=Proposal)
def handle_proposal_created(sender, instance, created, **kwargs):
    """
    Send proposal emails when a new proposal is submitted
    """
    if created:
        logger.info(f"New proposal submitted for project: {instance.project.title}")

        try:
            # Send confirmation email to freelancer
            send_proposal_submitted_email(instance)

            # Send notification email to client
            send_proposal_received_email(instance)

            # Update project proposals count
            instance.project.proposals_count = instance.project.proposals.count()
            instance.project.save(update_fields=['proposals_count'])

        except Exception as e:
            logger.error(f"Failed to send proposal emails for {instance.project.title}: {str(e)}")


@receiver(pre_save, sender=Proposal)
def handle_proposal_status_change(sender, instance, **kwargs):
    """
    Send proposal status update email when proposal status changes
    """
    if instance.pk:  # Only for existing proposals
        try:
            old_instance = Proposal.objects.get(pk=instance.pk)
            old_status = old_instance.status
            new_status = instance.status

            # Check if status actually changed
            if old_status != new_status:
                logger.info(f"Proposal for {instance.project.title} status changed from {old_status} to {new_status}")

                # Send status update email after the save completes
                from django.db import transaction
                transaction.on_commit(
                    lambda: send_proposal_status_update_email(instance, old_status, new_status)
                )
        except Proposal.DoesNotExist:
            logger.warning(f"Could not find existing proposal {instance.pk} for status change comparison")
        except Exception as e:
            logger.error(f"Error handling proposal status change: {str(e)}")


# -------------------------------
# Contract Related Signals
# -------------------------------

@receiver(post_save, sender=Contract)
def handle_contract_created(sender, instance, created, **kwargs):
    """
    Send contract creation emails when a new contract is created
    """
    if created:
        logger.info(f"New contract created: {instance.title}")

        try:
            # Send contract created emails to both client and freelancer
            send_contract_created_email(instance)

            # Send admin notification
            send_admin_contract_created_notification(instance)

            # Update project status to in_progress if it's not already
            if instance.project.status != 'in_progress':
                instance.project.status = 'in_progress'
                instance.project.save(update_fields=['status'])

        except Exception as e:
            logger.error(f"Failed to send contract created emails for {instance.title}: {str(e)}")


@receiver(pre_save, sender=Contract)
def handle_contract_status_change(sender, instance, **kwargs):
    """
    Send contract status update emails when contract status changes
    """
    if instance.pk:  # Only for existing contracts
        try:
            old_instance = Contract.objects.get(pk=instance.pk)
            old_status = old_instance.status
            new_status = instance.status

            # Check if status actually changed
            if old_status != new_status:
                logger.info(f"Contract {instance.title} status changed from {old_status} to {new_status}")

                # Send status update emails after the save completes
                from django.db import transaction
                transaction.on_commit(
                    lambda: send_contract_status_update_email(instance, old_status, new_status)
                )

                # Update project status based on contract status
                if new_status == 'completed':
                    instance.project.status = 'completed'
                    instance.project.save(update_fields=['status'])
                elif new_status == 'cancelled':
                    instance.project.status = 'cancelled'
                    instance.project.save(update_fields=['status'])

        except Contract.DoesNotExist:
            logger.warning(f"Could not find existing contract {instance.pk} for status change comparison")
        except Exception as e:
            logger.error(f"Error handling contract status change for {instance.title}: {str(e)}")


# -------------------------------
# Payment Related Signals
# -------------------------------

@receiver(post_save, sender=Payment)
def handle_payment_created(sender, instance, created, **kwargs):
    """
    Handle payment creation - mainly for due date reminders setup
    """
    if created:
        logger.info(f"New payment created for contract: {instance.contract.title}")

        # You might want to schedule due date reminders here
        # This would typically be handled by a task queue like Celery


@receiver(pre_save, sender=Payment)
def handle_payment_status_change(sender, instance, **kwargs):
    """
    Send payment completion email when payment status changes to completed
    """
    if instance.pk:  # Only for existing payments
        try:
            old_instance = Payment.objects.get(pk=instance.pk)
            old_status = old_instance.status
            new_status = instance.status

            # Check if status changed to completed
            if old_status != 'completed' and new_status == 'completed':
                logger.info(f"Payment completed for contract: {instance.contract.title}")

                # Set paid_date if not already set
                if not instance.paid_date:
                    from django.utils import timezone
                    instance.paid_date = timezone.now()

                # Send payment completion email after the save completes
                from django.db import transaction
                transaction.on_commit(
                    lambda: send_payment_completed_email(instance)
                )

                # Update freelancer's total earnings
                try:
                    freelancer_profile = instance.contract.freelancer.freelancer_profile
                    freelancer_profile.total_earnings += instance.amount
                    freelancer_profile.save(update_fields=['total_earnings'])
                except:
                    logger.warning(f"Could not update freelancer earnings for payment {instance.id}")

        except Payment.DoesNotExist:
            logger.warning(f"Could not find existing payment {instance.pk} for status change comparison")
        except Exception as e:
            logger.error(f"Error handling payment status change: {str(e)}")


# -------------------------------
# Review Related Signals
# -------------------------------

@receiver(post_save, sender=Review)
def handle_review_created(sender, instance, created, **kwargs):
    """
    Send review notification email when a new review is created
    """
    if created:
        logger.info(f"New review created for contract: {instance.contract.title}")

        try:
            # Send review notification email to reviewee
            send_review_received_email(instance)

            # Update reviewee's average rating
            update_user_rating(instance.reviewee)

        except Exception as e:
            logger.error(f"Failed to send review notification email: {str(e)}")


def update_user_rating(user):
    """
    Update user's average rating based on all reviews received
    """
    try:
        reviews = Review.objects.filter(reviewee=user)
        if reviews.exists():
            avg_rating = reviews.aggregate(avg_rating=models.Avg('rating'))['avg_rating']

            # Update freelancer profile rating if exists
            if hasattr(user, 'freelancer_profile'):
                user.freelancer_profile.rating = avg_rating or 0
                user.freelancer_profile.save(update_fields=['rating'])

            # Update company profile rating if exists
            if hasattr(user, 'company_profile'):
                user.company_profile.rating = avg_rating or 0
                user.company_profile.save(update_fields=['rating'])

    except Exception as e:
        logger.error(f"Error updating user rating for {user.email}: {str(e)}")


# -------------------------------
# Message Related Signals
# -------------------------------

@receiver(post_save, sender=Message)
def handle_message_created(sender, instance, created, **kwargs):
    """
    Send message notification email when a new message is created
    """
    if created:
        logger.info(f"New message sent from {instance.sender.email} to {instance.recipient.email}")

        try:
            # Send message notification email to recipient
            send_message_notification_email(instance)

            # Create a notification record
            Notification.objects.create(
                user=instance.recipient,
                notification_type='message_received',
                title=f'New message from {instance.sender.get_full_name() or instance.sender.email}',
                message=instance.message[:100] + "..." if len(instance.message) > 100 else instance.message,
                related_object_id=instance.id
            )

        except Exception as e:
            logger.error(f"Failed to send message notification email: {str(e)}")


# -------------------------------
# Notification Related Signals
# -------------------------------

@receiver(post_save, sender=Notification)
def handle_notification_created(sender, instance, created, **kwargs):
    """
    Handle notification creation - you can add additional logic here
    """
    if created:
        logger.info(f"New notification created for {instance.user.email}: {instance.title}")

        # You could send push notifications, SMS, or other alerts here
        # For now, we'll just log it


# -------------------------------
# Utility Functions for Manual Email Sending
# -------------------------------

def send_payment_reminder_emails():
    """
    Send payment due reminder emails for overdue payments
    This should be called by a scheduled task (like Celery beat)
    """
    from django.utils import timezone
    from datetime import timedelta

    # Get payments that are due tomorrow or overdue
    due_date = timezone.now().date() + timedelta(days=1)
    overdue_payments = Payment.objects.filter(
        status='pending',
        due_date__lte=due_date
    )

    success_count = 0
    failure_count = 0

    for payment in overdue_payments:
        try:
            success = send_payment_due_reminder_email(payment)
            if success:
                success_count += 1
            else:
                failure_count += 1
        except Exception as e:
            logger.error(f"Error sending payment reminder for payment {payment.id}: {str(e)}")
            failure_count += 1

    logger.info(f"Payment reminders sent: {success_count} success, {failure_count} failed")
    return success_count, failure_count


def send_project_update_notifications(project_id, message):
    """
    Send custom project update notifications to all stakeholders
    """
    try:
        project = Project.objects.get(id=project_id)

        # Get all users involved in the project (client + freelancers with proposals)
        recipients = [project.client]
        freelancers = [proposal.freelancer for proposal in project.proposals.all()]
        recipients.extend(freelancers)

        # Remove duplicates
        recipients = list(set(recipients))

        success_count = 0
        failure_count = 0

        context = {
            'project': project,
            'message': message,
            'project_url': f"{getattr(config, 'SITE_URL', '')}/projects/{project.id}/",
            'site_name': getattr(config, 'SITE_NAME', 'Mnory Freelance'),
            'support_email': getattr(config, 'ADMIN_EMAIL', 'support@mnory.com'),
        }

        for user in recipients:
            try:
                user_context = context.copy()
                user_context.update({
                    'user_name': user.get_full_name() or user.email.split('@')[0],
                })

                success = send_email_with_sendgrid(
                    to_email=user.email,
                    subject=f"Project Update - {project.title}",
                    template_name='project_update_notification',
                    context=user_context
                )

                if success:
                    success_count += 1
                else:
                    failure_count += 1

            except Exception as e:
                logger.error(f"Error sending project update notification to {user.email}: {str(e)}")
                failure_count += 1

        logger.info(f"Project update notifications sent: {success_count} success, {failure_count} failed")
        return success_count, failure_count

    except Project.DoesNotExist:
        logger.error(f"Project with ID {project_id} not found")
        return 0, 1
    except Exception as e:
        logger.error(f"Error sending project update notifications: {str(e)}")
        return 0, 1