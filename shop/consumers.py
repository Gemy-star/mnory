from __future__ import annotations

from typing import Any, Dict

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

from .models import Order, Message


class OrderChatConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for order-based chat.

    Group name convention matches shop.signals.handle_new_message:
    "order_<order_number>".
    """

    async def connect(self) -> None:
        self.order_number: str = self.scope["url_route"]["kwargs"]["order_number"]
        self.room_group_name: str = f"order_{self.order_number}"

        user = self.scope.get("user", AnonymousUser())
        try:
            self.order = await self._get_order()
        except Order.DoesNotExist:
            await self.close(code=4004)
            return

        is_allowed = await self._is_user_allowed(user)
        if not is_allowed:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code: int) -> None:
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive_json(self, content: Dict[str, Any], **kwargs: Any) -> None:
        """Handle incoming JSON messages from the client.

        Expected payload: {"body": "..."}
        """

        user = self.scope.get("user", AnonymousUser())
        if not user.is_authenticated:
            await self.send_json({"type": "error", "message": "auth_required"})
            return

        body = (content.get("body") or "").strip()
        if not body:
            return

        try:
            await self._create_message(user, body)
        except PermissionError:
            await self.send_json({"type": "error", "message": "not_allowed"})
        except Exception:
            # Generic failure – do not leak internals
            await self.send_json({"type": "error", "message": "server_error"})

    async def chat_message(self, event: Dict[str, Any]) -> None:
        """Receive a message event from the channel layer and send to WebSocket.

        shop.signals.handle_new_message sends events of this type.
        """

        message = event.get("message")
        if not message:
            return
        await self.send_json({"type": "chat_message", "message": message})

    # ------------------------------------------------------------------
    # DB helpers
    # ------------------------------------------------------------------

    @database_sync_to_async
    def _get_order(self) -> Order:
        return Order.objects.select_related("user").get(order_number=self.order_number)

    @database_sync_to_async
    def _is_user_allowed(self, user) -> bool:
        if not user.is_authenticated:
            return False
        if self.order.user_id == getattr(user, "id", None):
            return True
        # Vendor on any item in this order
        return self.order.items.filter(
            product_variant__product__vendor__user=user
        ).exists()

    @database_sync_to_async
    def _create_message(self, user, body: str) -> Message:
        """Create a Message instance for this order.

        Recipient logic mirrors shop.views.order_detail.
        """

        if not self._is_user_allowed_sync(user):
            raise PermissionError("User not allowed for this order")

        is_vendor = self.order.items.filter(
            product_variant__product__vendor__user=user
        ).exists()

        if is_vendor:
            recipient = self.order.user
        else:
            first_item = self.order.items.select_related(
                "product_variant__product__vendor__user"
            ).first()
            if first_item and first_item.product_variant.product.vendor:
                recipient = first_item.product_variant.product.vendor.user
            else:
                # Fallback to order user to avoid dropping the message silently
                recipient = self.order.user

        return Message.objects.create(
            order=self.order,
            sender=user,
            recipient=recipient,
            body=body,
        )

    def _is_user_allowed_sync(self, user) -> bool:
        if not user.is_authenticated:
            return False
        if self.order.user_id == getattr(user, "id", None):
            return True
        return self.order.items.filter(
            product_variant__product__vendor__user=user
        ).exists()
