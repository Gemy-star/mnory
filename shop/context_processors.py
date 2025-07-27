# shop/context_processors.py
from .models import Category
from django.urls import resolve
def categories_processor(request):
    return {
        'categories': Category.objects.filter(is_active=True).order_by('name'),
        'current_url_name': resolve(request.path_info).url_name,
    }