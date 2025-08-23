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

# Add this setting to be more strict about host validation
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Database: MariaDB (MySQL compatible)
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

STATIC_ROOT = os.path.join(BASE_DIR , 'staticfiles')
FILE_UPLOAD_TEMP_DIR = '/var/tmp/mnory'
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/mnory.log',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

STATIC_ROOT = os.path.join(BASE_DIR , "staticfiles")