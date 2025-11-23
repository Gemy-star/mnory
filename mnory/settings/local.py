from .common import *
import os


INSTALLED_APPS += [
    'silk',
]

MIDDLEWARE += ['silk.middleware.SilkyMiddleware',]


# Simple cache configuration for development.
# By default use local-memory cache; if REDIS_URL is set, we mirror the
# production Redis cache settings so behavior is closer to prod.
REDIS_CACHE_LOCATION = os.getenv('REDIS_URL')

if REDIS_CACHE_LOCATION:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_CACHE_LOCATION,
            'KEY_PREFIX': 'mnory_dev',
            'TIMEOUT': 60,  # shorter cache in dev
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'mnory-dev-cache',
        }
    }

