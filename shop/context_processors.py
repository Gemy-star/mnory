from itertools import chain


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
