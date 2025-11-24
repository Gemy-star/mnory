from .common import *
import os


INSTALLED_APPS += [
    'silk',
]

MIDDLEWARE += ['silk.middleware.SilkyMiddleware',]


# Simple cache configuration for development.
# By default use local-memory cache; if REDIS_URL is set, we mirror the
# production Redis cache settings so behavior is closer to prod.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'mnory-dev-cache',
    }
}

# Use in-memory channels layer in development to avoid needing Redis
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}

