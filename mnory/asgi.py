"""ASGI config for Mnory project with Django Channels support.

This exposes a ProtocolTypeRouter that handles both HTTP and WebSocket
connections. WebSocket routes are defined in ``mnory.routing``.
"""

import os
from dotenv import load_dotenv

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack


load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mnory.settings.production")


# Standard Django ASGI application (for HTTP)
django_asgi_app = get_asgi_application()

# Import project-level websocket routing
import mnory.routing  # noqa: E402


application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(
            URLRouter(mnory.routing.websocket_urlpatterns)
        ),
    }
)
