# urls.py for freelance app
from django.urls import path, include
from . import views

urlpatterns = [
    # Dashboard URLs
    path('', views.dashboard, name='dashboard'),
    path('freelancer-dashboard/', views.freelancer_dashboard, name='freelancer_dashboard'),
    path('company-dashboard/', views.company_dashboard, name='company_dashboard'),

    # Project URLs
    path('projects/', views.ProjectListView.as_view(), name='project_list'),
    path("projects/<uuid:pk>/", views.ProjectDetailView.as_view(), name="project_detail"),
    path('projects/create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('projects/<uuid:pk>/edit/', views.ProjectUpdateView.as_view(), name='project_edit'),

    # Proposal URLs
    path('projects/<uuid:project_id>/submit-proposal/', views.submit_proposal, name='submit_proposal'),
    path('proposals/<int:proposal_id>/', views.proposal_detail, name='proposal_detail'),
    path('proposals/<int:proposal_id>/accept/', views.accept_proposal, name='accept_proposal'),

    # Freelancer URLs
    path('freelancers/', views.FreelancerListView.as_view(), name='freelancer_list'),
    path('freelancers/<int:pk>/', views.FreelancerDetailView.as_view(), name='freelancer_detail'),
    path('freelancer/profile/create/', views.register_freelancer, name='create_freelancer_profile'),
    path('freelancer/profile/edit/', views.edit_freelancer_profile, name='edit_freelancer_profile'),

    # Company URLs
    path('companies/', views.CompanyListView.as_view(), name='company_list'),
    path('companies/<int:pk>/', views.CompanyDetailView.as_view(), name='company_detail'),
    path('company/profile/create/', views.register_company, name='create_company_profile'),
    path('company/profile/edit/', views.edit_company_profile, name='edit_company_profile'),

    # Contract URLs
    path('contracts/', views.contract_list, name='contract_list'),
    path('contracts/<uuid:pk>/', views.ContractDetailView.as_view(), name='contract_detail'),
    path('contracts/<uuid:contract_id>/complete/', views.complete_contract, name='complete_contract'),
    path('contracts/<uuid:contract_id>/payment/', views.create_payment, name='create_payment'),

    # Message URLs
    path('messages/', views.message_list, name='message_list'),
    path('messages/send/', views.send_message, name='send_message'),
    path('messages/send/<int:user_id>/', views.send_message, name='send_message_to_user'),
    path('messages/send/project/<uuid:project_id>/', views.send_message, name='send_message_project'),
    path('messages/send/contract/<uuid:contract_id>/', views.send_message, name='send_message_contract'),

    # Review URLs
    path('contracts/<uuid:contract_id>/review/', views.submit_review, name='submit_review'),

    # API URLs for AJAX requests
    path('api/notifications/', views.get_notifications, name='api_notifications'),
    path('api/notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/search/projects/', views.search_projects, name='search_projects'),
    path('api/search/freelancers/', views.search_freelancers, name='search_freelancers'),
]

