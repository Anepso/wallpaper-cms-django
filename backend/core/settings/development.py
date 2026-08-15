# core/settings/development.py
from .base import *
import os


DEBUG = True
ALLOWED_HOSTS = ['*']

# PostgreSQL Development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'wallpaper',
        'USER': 'postgres',
        'PASSWORD': 'PostgreSQL',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Tambahan untuk development
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'core/static')]
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')