"""
URL configuration for Mnory project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.contrib.admin.views.decorators import staff_member_required

from . import admin_views

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
]
if "rosetta" in settings.INSTALLED_APPS:
    urlpatterns += [
        re_path(r"^rosetta/", include("rosetta.urls")),
        path(
            "admin/translations/",
            staff_member_required(
                TemplateView.as_view(
                    template_name="admin/translation_dashboard_ajax.html"
                )
            ),
            name="admin_translation_dashboard",
        ),
        path(
            "admin/api/translations/",
            admin_views.translation_metadata,
            name="admin_translation_metadata",
        ),
        path(
            "admin/api/translations/<str:lang_code>/",
            admin_views.translation_messages,
            name="admin_translation_messages",
        ),
        path(
            "admin/api/translations/<str:lang_code>/update/",
            admin_views.translation_messages_update,
            name="admin_translation_messages_update",
        ),
    ]
if "constance" in settings.INSTALLED_APPS:
    urlpatterns += [
        path(
            "admin/settings/",
            staff_member_required(
                TemplateView.as_view(template_name="admin/settings_dashboard.html")
            ),
            name="admin_settings_dashboard",
        ),
        path(
            "admin/api/settings/",
            admin_views.constance_settings_list,
            name="admin_settings_metadata",
        ),
        path(
            "admin/api/settings/update/",
            admin_views.constance_settings_update,
            name="admin_settings_update",
        ),
    ]

urlpatterns += [
    path(
        "admin/chatbot/",
        staff_member_required(
            TemplateView.as_view(template_name="admin/chatbot_dashboard.html")
        ),
        name="admin_chatbot_dashboard",
    ),
    path(
        "admin/api/chatbot/questions/",
        admin_views.chatbot_questions_list,
        name="admin_chatbot_questions",
    ),
]
urlpatterns += i18n_patterns(
    path("", include("shop.urls")),  # Your main app
    path("jobs/", include("freelancing.urls")),  # Your freelancer app
    path("admin/", admin.site.urls),  # Django admin for superusers only
)

if settings.DEBUG:
    import silk

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += [path("silk/", include("silk.urls", namespace="silk"))]
