from itertools import chain
from .models import Category


def categories_processor(request):
    """
    Provides a list of all active categories to all templates.
    """
    categories = Category.objects.filter(is_active=True).order_by("name")
    return {"all_categories": categories}


def currency_processor(request):
    """
    Provides the user's selected currency to all templates.
    Defaults to USD if not set.
    """
    currency = request.session.get("currency", "USD")
    # Debug logging
    import logging

    logger = logging.getLogger(__name__)
    logger.info(
        f"Currency processor: session_key={request.session.session_key}, currency={currency}"
    )
    return {"currency": currency}


def notifications_context(request):
    """
    Provides notification-related context to all templates.
    """
    if not request.user.is_authenticated:
        return {}

    # Fetch notifications from both shop and freelancing apps
    shop_notifications = request.user.shop_notifications.all()
    freelancing_notifications = request.user.freelancing_notifications.all()

    # Combine and sort all notifications by creation date
    all_notifications = sorted(
        chain(shop_notifications, freelancing_notifications),
        key=lambda x: x.created_at,
        reverse=True,
    )

    # Get the count of unread notifications from both sources
    unread_count = sum(1 for n in all_notifications if not n.is_read)

    return {
        "recent_notifications": all_notifications[:10],  # Show the 10 most recent
        "unread_notifications_count": unread_count,
    }
