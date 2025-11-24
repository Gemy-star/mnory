from django.urls import re_path
from shop import consumers as shop_consumers

websocket_urlpatterns = [
    # WebSocket URL: wss://mnory.com/ws/orders/<order_number>/
    re_path(
        r"^ws/orders/(?P<order_number>[^/]+)/$",
        shop_consumers.OrderChatConsumer.as_asgi()
    ),
    # Direct user-to-user chat (e.g., admin ↔ user)
    re_path(
        r"^ws/user-chat/(?P<user_id>\d+)/$",
        shop_consumers.UserChatConsumer.as_asgi(),
    ),
]
