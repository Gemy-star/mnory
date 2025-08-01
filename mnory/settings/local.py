from .common import *


INSTALLED_APPS += [
    'silk',
]

MIDDLEWARE += ['silk.middleware.SilkyMiddleware',]


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mnory$mnorydb', # IMPORTANT: Use your actual username and database name
        'USER': 'mnory',                  # Your PythonAnywhere username
        'PASSWORD': 'admin123456',       # The password you set on the Databases tab
        'HOST': 'mnory.mysql.pythonanywhere-services.com', # The hostname from the Databases tab
        'PORT': '',                              # Leave empty for default MySQL port (3306)
    }
}