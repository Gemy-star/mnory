from django.urls import re_path

from shop import consumers as shop_consumers


websocket_urlpatterns = [
    # Order-based chat room: ws://<host>/ws/orders/<order_number>/
    re_path(r"^ws/orders/(?P<order_number>[^/]+)/$", shop_consumers.OrderChatConsumer.as_asgi()),
]
