# shop/context_processors.py
from .models import Category
from django.urls import resolve
from django.conf import settings
from django.contrib.sites.models import Site

def categories_processor(request):
    currency = request.session.get('currency', 'USD')
    current_site = Site.objects.get_current()

    return {
        'categories': Category.objects.filter(is_active=True).order_by('name'),
        'current_url_name': resolve(request.path_info).url_name,
        'currency':currency,
        'LANGUAGES': settings.LANGUAGES,
        'SITE_NAME': current_site.name,
        'SITE_URL': current_site.domain,
    }