"""
Django settings for varsity project.
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Force Django to use secure proxy headers (for Render)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-j=0lzhn=psi%7d&t+8$3s43u0r2j7u3ds$()z@bfa@on(*si+!')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Host settings
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.onrender.com', 'varsity-lygz.onrender.com']

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS = [
    'https://varsity-lygz.onrender.com',
    'https://*.onrender.com',
]

if DEBUG:
    CSRF_TRUSTED_ORIGINS += [
        'http://localhost:8000',
        'http://127.0.0.1:8000',
    ]

# ============ SIMPLE COOKIE SETTINGS THAT WORK EVERYWHERE ============
# Same exact settings for both local and Render - no more IF statements

# Let browser handle the domain - remove domain restriction
SESSION_COOKIE_DOMAIN = None
CSRF_COOKIE_DOMAIN = None

# Cookie security - set to work with both HTTP and HTTPS
SESSION_COOKIE_SECURE = False  # False works with both local and Render
CSRF_COOKIE_SECURE = False     # False works with both local and Render

# SameSite settings
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# Cookie paths - ensure they're sent everywhere
SESSION_COOKIE_PATH = '/'
CSRF_COOKIE_PATH = '/'

# HTTP-only settings
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # Must be False for admin to work

# Cookie ages
SESSION_COOKIE_AGE = 1209600  # 2 weeks
CSRF_COOKIE_AGE = 31449600    # 1 year

# Ensure session engine uses database
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'cloudinary',
    'cloudinary_storage',
    'posts',
    'accounts',
    'ganalytics',
    'resources',  # ADDED - Resources app for past papers and revision materials
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'varsity.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'varsity.wsgi.application'
ASGI_APPLICATION = 'varsity.asgi.application'

# Channel layers for WebSocket
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}

# Database
import dj_database_url
if 'DATABASE_URL' in os.environ:
    DATABASES = {
        'default': dj_database_url.config(conn_max_age=600)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Cloudinary configuration
import cloudinary
import cloudinary.uploader
import cloudinary.api

cloudinary.config(secure=True)

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Authentication settings
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'

# Cache for online users
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# ============ GOOGLE ANALYTICS ============
# Your actual Google Analytics Measurement ID
GANALYTICS_TRACKING_CODE = 'G-Z3MDMT6983'