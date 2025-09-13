# -------------------------------
# Freelance Platform Email Functions
# Add these to your main/email_utils.py file
# -------------------------------

# -------------------------------
# Freelancer Profile Emails
# -------------------------------
import logging

from constance import config

from freelancing.models import FreelancerProfile, CompanyProfile, Project, Proposal, Contract
from shop.email import send_email_with_sendgrid

logger = logging.getLogger(__name__)
def send_freelancer_registration_email(user, freelancer_profile):
    """
    Send registration confirmation email to newly registered freelancer
    """
    logger.info(f"Sending freelancer registration email to: {user.email}")

    try:
        context = {
            'user': user,
            'freelancer_profile': freelancer_profile,
            'freelancer_name': user.get_full_name() or user.email.split('@')[0],
            'title': freelancer_profile.title,
            'hourly_rate': freelancer_profile.hourly_rate,
            'email': user.email,
            'profile_url': f"{getattr(config, 'SITE_URL', '')}/freelancer/profile/{freelancer_profile.id}/",
            'dashboard_url': f"{getattr(config, 'SITE_URL', '')}/freelancer/dashboard/",
            'browse_projects_url': f"{getattr(config, 'SITE_URL', '')}/projects/",
            'site_name': getattr(config, 'SITE_NAME', 'Mnory Freelance'),
            'support_email': getattr(config, 'ADMIN_EMAIL', 'support@mnory.com'),
        }

        subject = f"Welcome to {getattr(config, 'SITE_NAME', 'Mnory Freelance')} - Freelancer Registration Complete"

        success = send_email_with_sendgrid(
            to_email=user.email,
            subject=subject,
            template_name='freelancer_registration',
            context=context
        )

        if success:
            logger.info(f"Freelancer registration email sent successfully to: {user.email}")
        else:
            logger.error(f"Failed to send freelancer registration email to: {user.email}")

        return success

    except Exception as e:
        logger.exception(f"Error sending freelancer registration email to {user.email}: {str(e)}")
        return False


def send_freelancer_verification_email(user, freelancer_profile):
    """
    Send verification confirmation email to verified freelancer
    """
    logger.info(f"Sending freelancer verification email to: {user.email}")

    try:
        context = {
            'user': user,
            'freelancer_profile': freelancer_profile,
            'freelancer_name': user.get_full_name() or user.email.split('@')[0],
            'title': freelancer_profile.title,
            'profile_url': f"{getattr(config, 'SITE_URL', '')}/freelancer/profile/{freelancer_profile.id}/",
            'dashboard_url': f"{getattr(config, 'SITE_URL', '')}/freelancer/dashboard/",
            'site_name': getattr(config, 'SITE_NAME', 'Mnory Freelance'),
            'support_email': getattr(config, 'ADMIN_EMAIL', 'support@mnory.com'),
        }

        subject = "Congratulations! Your freelancer profile has been verified"

        success = send_email_with_sendgrid(
            to_email=user.email,
            subject=subject,
            template_name='freelancer_verification',
            context=context
        )

        if success:
            logger.info(f"Freelancer verification email sent successfully to: {user.email}")
        else:
            logger.error(f"Failed to send freelancer verification email to: {user.email}")

        return success

    except Exception as e:
        logger.exception(f"Error sending freelancer verification email to {user.email}: {str(e)}")
        return False


# -------------------------------
# Company Profile Emails
# -------------------------------

def send_company_registration_email(user, company_profile):
    """
    Send registration confirmation email to newly registered company
    """
    logger.info(f"Sending company registration email to: {user.email}")

    try:
        context = {
            'user': user,
            'company_profile': company_profile,
            'company_name': company_profile.company_name,
            'company_email': user.email,
            'industry': company_profile.industry,
            'company_size': company_profile.get_company_size_display(),
            'location': company_profile.location,
            'registration_date': company_profile.created_at,
            'admin_url': f"{getattr(config, 'SITE_URL', '')}/admin/freelance/companyprofile/{company_profile.id}/",
            'site_name': getattr(config, 'SITE_NAME', 'Mnory Freelance'),
        }

        subject = f"New Company Registration - {company_profile.company_name}"

        success = send_email_with_sendgrid(
            to_email=config.ADMIN_EMAIL,
            subject=subject,
            template_name='admin_new_company',
            context=context
        )

        if success:
            logger.info(f"Admin new company notification sent successfully for: {user.email}")
        else:
            logger.error(f"Failed to send admin new company notification for: {user.email}")

        return success

    except Exception as e:
        logger.exception(f"Error sending admin new company notification for {user.email}: {str(e)}")
        return False


def send_admin_new_project_notification(project):
    """
    Send new project notification to admin
    """
    logger.info(f"Sending new project notification to admin for: {project.title}")

    try:
        admin_email = getattr(config, 'ADMIN_EMAIL', None)
        if not admin_email:
            logger.error("No admin email configured")
            return False

        context = {
            'project': project,
            'project_title': project.title,
            'client_name': project.client.get_full_name() or project.client.email.split('@')[0],
            'client_email': project.client.email,
            'category': project.category.name,
            'project_type': project.get_project_type_display(),
            'budget_range': f"${project.budget_min} - ${project.budget_max}" if project.budget_min and project.budget_max else "Not specified",
            'created_date': project.created_at,
            'admin_url': f"{getattr(config, 'SITE_URL', '')}/admin/freelance/project/{project.id}/",
            'project_url': f"{getattr(config, 'SITE_URL', '')}/projects/{project.id}/",
            'site_name': getattr(config, 'SITE_NAME', 'Mnory Freelance'),
        }

        subject = f"New Project Posted - {project.title}"

        success = send_email_with_sendgrid(
            to_email=admin_email,
            subject=subject,
            template_name='admin_new_project',
            context=context
        )

        if success:
            logger.info(f"Admin new project notification sent successfully for: {project.title}")
        else:
            logger.error(f"Failed to send admin new project notification for: {project.title}")

        return success

    except Exception as e:
        logger.exception(f"Error sending admin new project notification for {project.title}: {str(e)}")
        return False


def send_admin_contract_created_notification(contract):
    """
    Send contract creation notification to admin
    """
    logger.info(f"Sending contract created notification to admin for: {contract.title}")

    try:
        admin_email = getattr(config, 'ADMIN_EMAIL', None)
        if not admin_email:
            logger.error("No admin email configured")
            return False

        context = {
            'contract': contract,
            'contract_title': contract.title,
            'project_title': contract.project.title,
            'client_name': contract.client.get_full_name() or contract.client.email.split('@')[0],
            'freelancer_name': contract.freelancer.get_full_name() or contract.freelancer.email.split('@')[0],
            'amount': contract.amount,
            'start_date': contract.start_date,
            'created_date': contract.created_at,
            'admin_url': f"{getattr(config, 'SITE_URL', '')}/admin/freelance/contract/{contract.id}/",
            'contract_url': f"{getattr(config, 'SITE_URL', '')}/contracts/{contract.id}/",
            'site_name': getattr(config, 'SITE_NAME', 'Mnory Freelance'),
        }

        subject = f"New Contract Created - {contract.title}"

        success = send_email_with_sendgrid(
            to_email=admin_email,
            subject=subject,
            template_name='admin_contract_created',
            context=context
        )

        if success:
            logger.info(f"Admin contract created notification sent successfully for: {contract.title}")
        else:
            logger.error(f"Failed to send admin contract created notification for: {contract.title}")

        return success

    except Exception as e:
        logger.exception(f"Error sending admin contract created notification for {contract.title}: {str(e)}")
        return False


# -------------------------------
# Test Functions
# -------------------------------

def test_freelancer_registration_email(freelancer_profile_id):
    """
    Test freelancer registration email for a specific freelancer profile
    """
    try:
        freelancer_profile = FreelancerProfile.objects.get(id=freelancer_profile_id)
        success = send_freelancer_registration_email(freelancer_profile.user, freelancer_profile)
        print(f"Freelancer registration email test: {'✅ Success' if success else '❌ Failed'}")
        return success
    except FreelancerProfile.DoesNotExist:
        print(f"❌ Freelancer profile with ID {freelancer_profile_id} not found")
        return False
    except Exception as e:
        print(f"❌ Error testing freelancer registration email: {str(e)}")
        return False


def test_company_registration_email(company_profile_id):
    """
    Test company registration email for a specific company profile
    """
    try:
        company_profile = CompanyProfile.objects.get(id=company_profile_id)
        success = send_company_registration_email(company_profile.user, company_profile)
        print(f"Company registration email test: {'✅ Success' if success else '❌ Failed'}")
        return success
    except CompanyProfile.DoesNotExist:
        print(f"❌ Company profile with ID {company_profile_id} not found")
        return False
    except Exception as e:
        print(f"❌ Error testing company registration email: {str(e)}")
        return False


def test_project_posted_email(project_id):
    """
    Test project posted email for a specific project
    """
    try:
        project = Project.objects.get(id=project_id)
        success = send_project_posted_email(project)
        print(f"Project posted email test: {'✅ Success' if success else '❌ Failed'}")
        return success
    except Project.DoesNotExist:
        print(f"❌ Project with ID {project_id} not found")
        return False
    except Exception as e:
        print(f"❌ Error testing project posted email: {str(e)}")
        return False


def test_proposal_submitted_email(proposal_id):
    """
    Test proposal submitted email for a specific proposal
    """
    try:
        proposal = Proposal.objects.get(id=proposal_id)
        success = send_proposal_submitted_email(proposal)
        print(f"Proposal submitted email test: {'✅ Success' if success else '❌ Failed'}")
        return success
    except Proposal.DoesNotExist:
        print(f"❌ Proposal with ID {proposal_id} not found")
        return False
    except Exception as e:
        print(f"❌ Error testing proposal submitted email: {str(e)}")
        return False


def test_contract_created_email(contract_id):
    """
    Test contract created email for a specific contract.
    """
    try:
        contract = Contract.objects.get(id=contract_id)
        success = send_contract_created_email(contract)
        logger.info(f"Contract created email test: {'✅ Success' if success else '❌ Failed'}")
        return success
    except Contract.DoesNotExist:
        logger.error(f"❌ Contract with ID {contract_id} not found")
        return False
    except Exception as e:
        logger.error(f"❌ Error testing contract created email: {str(e)}")
        return False


def send_company_registration_email(user, company_profile):
    """
    Send company registration email to the user.
    """
    try:
        context = {
            'company_name': company_profile.company_name,
            'industry': company_profile.industry,
            'company_size': company_profile.get_company_size_display(),
            'email': user.email,
            'dashboard_url': f"{getattr(config, 'SITE_URL', '')}/company/dashboard/",
            'post_project_url': f"{getattr(config, 'SITE_URL', '')}/projects/create/",
            'browse_freelancers_url': f"{getattr(config, 'SITE_URL', '')}/freelancers/",
            'site_name': getattr(config, 'SITE_NAME', 'Mnory Freelance'),
            'support_email': getattr(config, 'ADMIN_EMAIL', 'support@mnory.com'),
        }

        subject = f"Welcome to {getattr(config, 'SITE_NAME', 'Mnory Freelance')} - Company Registration Complete"

        success = send_email_with_sendgrid(
            to_email=user.email,
            subject=subject,
            template_name='company_registration',
            context=context
        )

        if success:
            logger.info(f"Company registration email sent successfully to: {user.email}")
        else:
            logger.error(f"Failed to send company registration email to: {user.email}")

        return success

    except Exception as e:
        logger.exception(f"Error sending company registration email to {user.email}: {str(e)}")
        return False


def send_company_verification_email(user, company_profile):
    """
    Send verification confirmation email to verified company
    """
    logger.info(f"Sending company verification email to: {user.email}")

    try:
        context = {
            'user': user,
            'company_profile': company_profile,
            'company_name': company_profile.company_name,
            'dashboard_url': f"{getattr(config, 'SITE_URL', '')}/company/dashboard/",
            'post_project_url': f"{getattr(config, 'SITE_URL', '')}/projects/create/",
            'site_name': getattr(config, 'SITE_NAME', 'Mnory Freelance'),
            'support_email': getattr(config, 'ADMIN_EMAIL', 'support@mnory.com'),
        }

        subject = "Congratulations! Your company profile has been verified"

        success = send_email_with_sendgrid(
            to_email=user.email,
            subject=subject,
            template_name='company_verification',
            context=context
        )

        if success:
            logger.info(f"Company verification email sent successfully to: {user.email}")
        else:
            logger.error(f"Failed to send company verification email to: {user.email}")

        return success

    except Exception as e:
        logger.exception(f"Error sending company verification email to {user.email}: {str(e)}")
        return False


# -------------------------------
# Project Related Emails
# -------------------------------

def send_project_posted_email(project):
    """
    Send confirmation email to client when project is posted
    """
    logger.info(f"Sending project posted email for: {project.title}")

    try:
        context = {
            'project': project,
            'client_name': project.client.get_full_name() or project.client.email.split('@')[0],
            'project_title': project.title,
            'project_type': project.get_project_type_display(),
            'category': project.category.name,
            'project_url': f"{getattr(config, 'SITE_URL', '')}/projects/{project.id}/",
            'manage_projects_url': f"{getattr(config, 'SITE_URL', '')}/company/projects/",
            'site_name': getattr(config, 'SITE_NAME', 'Mnory Freelance'),
            'support_email': getattr(config, 'ADMIN_EMAIL', 'support@mnory.com'),
        }

        subject = f"Project Posted Successfully - {project.title}"

        success = send_email_with_sendgrid(
            to_email=project.client.email,
            subject=subject,
            template_name='project_posted',
            context=context
        )

        if success:
            logger.info(f"Project posted email sent successfully for: {project.title}")
        else:
            logger.error(f"Failed to send project posted email for: {project.title}")

        return success

    except Exception as e:
        logger.exception(f"Error sending project posted email for {project.title}: {str(e)}")
        return False


def send_project_status_update_email(project, old_status, new_status):
    """
    Send project status update email to client
    """
    logger.info(f"Sending project status update email for: {project.title}")

    try:
        context = {
            'project': project,
            'client_name': project.client.get_full_name() or project.client.email.split('@')[0],
            'project_title': project.title,
            'old_status': old_status,
            'new_status': new_status,
            'status_display': project.get_status_display(),
            'project_url': f"{getattr(config, 'SITE_URL', '')}/projects/{project.id}/",
            'site_name': getattr(config, 'SITE_NAME', 'Mnory Freelance'),
            'support_email': getattr(config, 'ADMIN_EMAIL', 'support@mnory.com'),
        }

        subject = f"Project Update - {project.title} is now {project.get_status_display()}"

        success = send_email_with_sendgrid(
            to_email=project.client.email,
            subject=subject,
            template_name='project_status_update',
            context=context
        )

        if success:
            logger.info(f"Project status update email sent successfully for: {project.title}")
        else:
            logger.error(f"Failed to send project status update email for: {project.title}")

        return success

    except Exception as e:
        logger.exception(f"Error sending project status update email for {project.title}: {str(e)}")
        return False


# -------------------------------
# Proposal Related Emails
# -------------------------------

def send_proposal_submitted_email(proposal):
    """
    Send confirmation email to freelancer when proposal is submitted
    """
    logger.info(f"Sending proposal submitted email for project: {proposal.project.title}")

    try:
        context = {
            'proposal': proposal,
            'freelancer_name': proposal.freelancer.get_full_name() or proposal.freelancer.email.split('@')[0],
            'project_title': proposal.project.title,
            'client_name': proposal.project.client.get_full_name() or proposal.project.client.email.split('@')[0],
            'proposed_amount': proposal.proposed_amount,
            'estimated_duration': proposal.estimated_duration,
            'project_url': f"{getattr(config, 'SITE_URL', '')}/projects/{proposal.project.id}/",
            'proposals_url': f"{getattr(config, 'SITE_URL', '')}/freelancer/proposals/",
            'site_name': getattr(config, 'SITE_NAME', 'Mnory Freelance'),
            'support_email': getattr(config, 'ADMIN_EMAIL', 'support@mnory.com'),
        }

        subject = f"Proposal Submitted - {proposal.project.title}"

        success = send_email_with_sendgrid(
            to_email=proposal.freelancer.email,
            subject=subject,
            template_name='proposal_submitted.txt',
            context=context
        )

        if success:
            logger.info(f"Proposal submitted email sent successfully to: {proposal.freelancer.email}")
        else:
            logger.error(f"Failed to send proposal submitted email to: {proposal.freelancer.email}")

        return success

    except Exception as e:
        logger.exception(f"Error sending proposal submitted email: {str(e)}")
        return False


def send_proposal_received_email(proposal):
    """
    Send notification email to client when new proposal is received
    """
    logger.info(f"Sending proposal received email to client for project: {proposal.project.title}")

    try:
        context = {
            'proposal': proposal,
            'client_name': proposal.project.client.get_full_name() or proposal.project.client.email.split('@')[0],
            'project_title': proposal.project.title,
            'freelancer_name': proposal.freelancer.get_full_name() or proposal.freelancer.email.split('@')[0],
            'proposed_amount': proposal.proposed_amount,
            'estimated_duration': proposal.estimated_duration,
            'project_url': f"{getattr(config, 'SITE_URL', '')}/projects/{proposal.project.id}/",
            'proposals_url': f"{getattr(config, 'SITE_URL', '')}/projects/{proposal.project.id}/proposals/",
            'site_name': getattr(config, 'SITE_NAME', 'Mnory Freelance'),
            'support_email': getattr(config, 'ADMIN_EMAIL', 'support@mnory.com'),
        }

        subject = f"New Proposal Received - {proposal.project.title}"

        success = send_email_with_sendgrid(
            to_email=proposal.project.client.email,
            subject=subject,
            template_name='proposal_received',
            context=context
        )

        if success:
            logger.info(f"Proposal received email sent successfully to: {proposal.project.client.email}")
        else:
            logger.error(f"Failed to send proposal received email to: {proposal.project.client.email}")

        return success

    except Exception as e:
        logger.exception(f"Error sending proposal received email: {str(e)}")
        return False


def send_proposal_status_update_email(proposal, old_status, new_status):
    """
    Send proposal status update email to freelancer
    """
    logger.info(f"Sending proposal status update email for: {proposal.project.title}")

    try:
        context = {
            'proposal': proposal,
            'freelancer_name': proposal.freelancer.get_full_name() or proposal.freelancer.email.split('@')[0],
            'project_title': proposal.project.title,
            'client_name': proposal.project.client.get_full_name() or proposal.project.client.email.split('@')[0],
            'old_status': old_status,
            'new_status': new_status,
            'status_display': proposal.get_status_display(),
            'project_url': f"{getattr(config, 'SITE_URL', '')}/projects/{proposal.project.id}/",
            'site_name': getattr(config, 'SITE_NAME', 'Mnory Freelance'),
            'support_email': getattr(config, 'ADMIN_EMAIL', 'support@mnory.com'),
        }

        subject = f"Proposal Update - {proposal.project.title}"

        success = send_email_with_sendgrid(
            to_email=proposal.freelancer.email,
            subject=subject,
            template_name='proposal_status_update',
            context=context
        )

        if success:
            logger.info(f"Proposal status update email sent successfully to: {proposal.freelancer.email}")
        else:
            logger.error(f"Failed to send proposal status update email to: {proposal.freelancer.email}")

        return success

    except Exception as e:
        logger.exception(f"Error sending proposal status update email: {str(e)}")
        return False


# -------------------------------
# Contract Related Emails
# -------------------------------

def send_contract_created_email(contract):
    """
    Send contract creation email to both client and freelancer
    """
    logger.info(f"Sending contract created emails for: {contract.title}")

    try:
        base_context = {
            'contract': contract,
            'project_title': contract.project.title,
            'amount': contract.amount,
            'start_date': contract.start_date,
            'end_date': contract.end_date,
            'contract_url': f"{getattr(config, 'SITE_URL', '')}/contracts/{contract.id}/",
            'site_name': getattr(config, 'SITE_NAME', 'Mnory Freelance'),
            'support_email': getattr(config, 'ADMIN_EMAIL', 'support@mnory.com'),
        }

        # Email to client
        client_context = base_context.copy()
        client_context.update({
            'client_name': contract.client.get_full_name() or contract.client.email.split('@')[0],
            'freelancer_name': contract.freelancer.get_full_name() or contract.freelancer.email.split('@')[0],
            'recipient_type': 'client'
        })

        client_success = send_email_with_sendgrid(
            to_email=contract.client.email,
            subject=f"Contract Created - {contract.title}",
            template_name='contract_created',
            context=client_context
        )

        # Email to freelancer
        freelancer_context = base_context.copy()
        freelancer_context.update({
            'freelancer_name': contract.freelancer.get_full_name() or contract.freelancer.email.split('@')[0],
            'client_name': contract.client.get_full_name() or contract.client.email.split('@')[0],
            'recipient_type': 'freelancer'
        })

        freelancer_success = send_email_with_sendgrid(
            to_email=contract.freelancer.email,
            subject=f"Contract Created - {contract.title}",
            template_name='contract_created',
            context=freelancer_context
        )

        success = client_success and freelancer_success

        if success:
            logger.info(f"Contract created emails sent successfully for: {contract.title}")
        else:
            logger.error(f"Failed to send one or more contract created emails for: {contract.title}")

        return success

    except Exception as e:
        logger.exception(f"Error sending contract created emails for {contract.title}: {str(e)}")
        return False


def send_contract_status_update_email(contract, old_status, new_status):
    """
    Send contract status update email to both parties
    """
    logger.info(f"Sending contract status update emails for: {contract.title}")

    try:
        base_context = {
            'contract': contract,
            'project_title': contract.project.title,
            'old_status': old_status,
            'new_status': new_status,
            'status_display': contract.get_status_display(),
            'contract_url': f"{getattr(config, 'SITE_URL', '')}/contracts/{contract.id}/",
            'site_name': getattr(config, 'SITE_NAME', 'Mnory Freelance'),
            'support_email': getattr(config, 'ADMIN_EMAIL', 'support@mnory.com'),
        }

        # Email to client
        client_context = base_context.copy()
        client_context.update({
            'client_name': contract.client.get_full_name() or contract.client.email.split('@')[0],
            'freelancer_name': contract.freelancer.get_full_name() or contract.freelancer.email.split('@')[0],
        })

        client_success = send_email_with_sendgrid(
            to_email=contract.client.email,
            subject=f"Contract Update - {contract.title}",
            template_name='contract_status_update',
            context=client_context
        )

        # Email to freelancer
        freelancer_context = base_context.copy()
        freelancer_context.update({
            'freelancer_name': contract.freelancer.get_full_name() or contract.freelancer.email.split('@')[0],
            'client_name': contract.client.get_full_name() or contract.client.email.split('@')[0],
        })

        freelancer_success = send_email_with_sendgrid(
            to_email=contract.freelancer.email,
            subject=f"Contract Update - {contract.title}",
            template_name='contract_status_update',
            context=freelancer_context
        )

        success = client_success and freelancer_success

        if success:
            logger.info(f"Contract status update emails sent successfully for: {contract.title}")
        else:
            logger.error(f"Failed to send contract status update emails for: {contract.title}")

        return success

    except Exception as e:
        logger.exception(f"Error sending contract status update emails for {contract.title}: {str(e)}")
        return False


# -------------------------------
# Payment Related Emails
# -------------------------------

def send_payment_completed_email(payment):
    """
    Send payment completion email to freelancer
    """
    logger.info(f"Sending payment completed email for contract: {payment.contract.title}")

    try:
        context = {
            'payment': payment,
            'freelancer_name': payment.contract.freelancer.get_full_name() or
                               payment.contract.freelancer.email.split('@')[0],
            'client_name': payment.contract.client.get_full_name() or payment.contract.client.email.split('@')[0],
            'contract_title': payment.contract.title,
            'amount': payment.amount,
            'payment_type': payment.get_payment_type_display(),
            'paid_date': payment.paid_date,
            'transaction_id': payment.transaction_id,
            'contract_url': f"{getattr(config, 'SITE_URL', '')}/contracts/{payment.contract.id}/",
            'site_name': getattr(config, 'SITE_NAME', 'Mnory Freelance'),
            'support_email': getattr(config, 'ADMIN_EMAIL', 'support@mnory.com'),
        }

        subject = f"Payment Received - {payment.contract.title}"

        success = send_email_with_sendgrid(
            to_email=payment.contract.freelancer.email,
            subject=subject,
            template_name='payment_completed',
            context=context
        )

        if success:
            logger.info(f"Payment completed email sent successfully to: {payment.contract.freelancer.email}")
        else:
            logger.error(f"Failed to send payment completed email to: {payment.contract.freelancer.email}")

        return success

    except Exception as e:
        logger.exception(f"Error sending payment completed email: {str(e)}")
        return False


def send_payment_due_reminder_email(payment):
    """
    Send payment due reminder email to client
    """
    logger.info(f"Sending payment due reminder for contract: {payment.contract.title}")

    try:
        context = {
            'payment': payment,
            'client_name': payment.contract.client.get_full_name() or payment.contract.client.email.split('@')[0],
            'freelancer_name': payment.contract.freelancer.get_full_name() or
                               payment.contract.freelancer.email.split('@')[0],
            'contract_title': payment.contract.title,
            'amount': payment.amount,
            'due_date': payment.due_date,
            'payment_type': payment.get_payment_type_display(),
            'contract_url': f"{getattr(config, 'SITE_URL', '')}/contracts/{payment.contract.id}/",
            'payment_url': f"{getattr(config, 'SITE_URL', '')}/payments/{payment.id}/pay/",
            'site_name': getattr(config, 'SITE_NAME', 'Mnory Freelance'),
            'support_email': getattr(config, 'ADMIN_EMAIL', 'support@mnory.com'),
        }

        subject = f"Payment Due Reminder - {payment.contract.title}"

        success = send_email_with_sendgrid(
            to_email=payment.contract.client.email,
            subject=subject,
            template_name='payment_due_reminder',
            context=context
        )

        if success:
            logger.info(f"Payment due reminder sent successfully to: {payment.contract.client.email}")
        else:
            logger.error(f"Failed to send payment due reminder to: {payment.contract.client.email}")

        return success

    except Exception as e:
        logger.exception(f"Error sending payment due reminder: {str(e)}")
        return False


# -------------------------------
# Review Related Emails
# -------------------------------

def send_review_received_email(review):
    """
    Send review notification email to reviewee
    """
    logger.info(f"Sending review received email for contract: {review.contract.title}")

    try:
        context = {
            'review': review,
            'reviewee_name': review.reviewee.get_full_name() or review.reviewee.email.split('@')[0],
            'reviewer_name': review.reviewer.get_full_name() or review.reviewer.email.split('@')[0],
            'contract_title': review.contract.title,
            'rating': review.rating,
            'comment': review.comment,
            'contract_url': f"{getattr(config, 'SITE_URL', '')}/contracts/{review.contract.id}/",
            'profile_url': f"{getattr(config, 'SITE_URL', '')}/freelancer/profile/{review.reviewee.id}/" if hasattr(
                review.reviewee,
                'freelancer_profile') else f"{getattr(config, 'SITE_URL', '')}/company/profile/{review.reviewee.id}/",
            'site_name': getattr(config, 'SITE_NAME', 'Mnory Freelance'),
            'support_email': getattr(config, 'ADMIN_EMAIL', 'support@mnory.com'),
        }

        subject = f"New Review Received - {review.contract.title}"

        success = send_email_with_sendgrid(
            to_email=review.reviewee.email,
            subject=subject,
            template_name='review_received',
            context=context
        )

        if success:
            logger.info(f"Review received email sent successfully to: {review.reviewee.email}")
        else:
            logger.error(f"Failed to send review received email to: {review.reviewee.email}")

        return success

    except Exception as e:
        logger.exception(f"Error sending review received email: {str(e)}")
        return False


# -------------------------------
# Message Related Emails
# -------------------------------

def send_message_notification_email(message):
    """
    Send message notification email to recipient
    """
    logger.info(f"Sending message notification email to: {message.recipient.email}")

    try:
        context = {
            'message': message,
            'recipient_name': message.recipient.get_full_name() or message.recipient.email.split('@')[0],
            'sender_name': message.sender.get_full_name() or message.sender.email.split('@')[0],
            'subject': message.subject,
            'message_preview': message.message[:150] + "..." if len(message.message) > 150 else message.message,
            'project_title': message.project.title if message.project else None,
            'contract_title': message.contract.title if message.contract else None,
            'messages_url': f"{getattr(config, 'SITE_URL', '')}/messages/",
            'site_name': getattr(config, 'SITE_NAME', 'Mnory Freelance'),
            'support_email': getattr(config, 'ADMIN_EMAIL', 'support@mnory.com'),
        }

        subject = f"New Message - {message.subject}" if message.subject else "New Message Received"

        success = send_email_with_sendgrid(
            to_email=message.recipient.email,
            subject=subject,
            template_name='message_notification',
            context=context
        )

        if success:
            logger.info(f"Message notification email sent successfully to: {message.recipient.email}")
        else:
            logger.error(f"Failed to send message notification email to: {message.recipient.email}")

        return success

    except Exception as e:
        logger.exception(f"Error sending message notification email: {str(e)}")
        return False


# -------------------------------
# Admin Notification Emails
# -------------------------------

def send_admin_new_freelancer_notification(user, freelancer_profile):
    """
    Send new freelancer registration notification to admin
    """
    logger.info(f"Sending new freelancer notification to admin for: {user.email}")

    try:
        admin_email = getattr(config, 'ADMIN_EMAIL', None)
        if not admin_email:
            logger.error("No admin email configured")
            return False

        context = {
            'user': user,
            'freelancer_profile': freelancer_profile,
            'freelancer_name': user.get_full_name() or user.email.split('@')[0],
            'freelancer_email': user.email,
            'title': freelancer_profile.title,
            'hourly_rate': freelancer_profile.hourly_rate,
            'experience_level': freelancer_profile.get_experience_level_display(),
            'registration_date': freelancer_profile.created_at,
            'admin_url': f"{getattr(config, 'SITE_URL', '')}/admin/freelance/freelancerprofile/{freelancer_profile.id}/",
            'site_name': getattr(config, 'SITE_NAME', 'Mnory Freelance'),
        }

        subject = f"New Freelancer Registration - {freelancer_profile.title}"

        success = send_email_with_sendgrid(
            to_email=admin_email,
            subject=subject,
            template_name='admin_new_freelancer',
            context=context
        )

        if success:
            logger.info(f"Admin new freelancer notification sent successfully for: {user.email}")
        else:
            logger.error(f"Failed to send admin new freelancer notification for: {user.email}")

        return success

    except Exception as e:
        logger.exception(f"Error sending admin new freelancer notification for {user.email}: {str(e)}")
        return False

def send_admin_new_company_notification(user, company_profile):
    """
    Send new company registration notification to admin
    """
    logger.info(f"Sending new company notification to admin for: {user.email}")

    try:
        admin_email = getattr(config, 'ADMIN_EMAIL', None)
        if not admin_email:
            logger.error("No admin email configured")
            return False

        context = {
            'user': user,
            'company_profile': company_profile,
            'company_name': company_profile.company_name,
            'company_email': user.email,
            'industry': company_profile.industry,
            'company_size': company_profile.get_company_size_display(),
            'location': company_profile.location,
            'website_url': company_profile.website_url,
            'founded_year': company_profile.founded_year,
            'registration_date': company_profile.created_at,
            'admin_url': f"{getattr(config, 'SITE_URL', '')}/admin/freelance/companyprofile/{company_profile.id}/",
            'company_profile_url': f"{getattr(config, 'SITE_URL', '')}/company/profile/{company_profile.id}/",
            'site_name': getattr(config, 'SITE_NAME', 'Mnory Freelance'),
        }

        subject = f"New Company Registration - {company_profile.company_name}"

        success = send_email_with_sendgrid(
            to_email=admin_email,
            subject=subject,
            template_name='admin_new_company',
            context=context
        )

        if success:
            logger.info(f"Admin new company notification sent successfully for: {user.email}")
        else:
            logger.error(f"Failed to send admin new company notification for: {user.email}")

        return success

    except Exception as e:
        logger.exception(f"Error sending admin new company notification for {user.email}: {str(e)}")
        return False