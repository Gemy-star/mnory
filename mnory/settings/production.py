from .common import *
import os

DEBUG = False

ALLOWED_HOSTS = [
    'mnory.com',
    'www.mnory.com',
    'localhost',
    '127.0.0.1',
    '45.9.191.23',
]

# Ensure Django respects proxy headers (for HTTPS behind Nginx)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# =======================
# Database: MariaDB
# =======================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'mnorydb'),
        'USER': os.getenv('DB_USER', 'mnory'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'Gemy@24765202'),
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        'CONN_MAX_AGE': 60,
    }
}

# =======================
# Redis cache & sessions
# =======================

# Use Redis for Django cache in production. LOCATION can be overridden
# via REDIS_URL env var, e.g. redis://127.0.0.1:6379/1
REDIS_CACHE_LOCATION = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_CACHE_LOCATION,
        'KEY_PREFIX': 'mnory',
        'TIMEOUT': 300,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
    }
}

# Store sessions in both cache (Redis) and DB for resilience
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_CACHE_ALIAS = 'default'

# =======================
# Static & Media
# =======================
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
FILE_UPLOAD_TEMP_DIR = '/var/tmp/mnory'

# =======================
# Channels: Redis channel layer
# =======================

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}

# =======================
# Logging
# =======================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.getenv('DJANGO_LOG_FILE', '/var/log/django/mnory.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}


