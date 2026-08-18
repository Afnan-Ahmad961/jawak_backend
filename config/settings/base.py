"""
Base Django settings for the Jawak backend.

Settings common to every environment live here. Environment-specific
overrides (DEBUG, ALLOWED_HOSTS, security hardening, etc.) live in
`development.py` and `production.py`, which each start with
`from .base import *`.

For more information, see
https://docs.djangoproject.com/en/6.0/topics/settings/
"""

from datetime import timedelta
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# base.py lives at config/settings/base.py, so the project root is three
# levels up.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# Security
# SECRET_KEY is read from the environment in every environment.
SECRET_KEY = os.getenv('SECRET_KEY')

# DEBUG and ALLOWED_HOSTS are defined per-environment (see development.py /
# production.py).


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # Third-party
    'rest_framework',
    'dj_rest_auth',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'dj_rest_auth.registration',
    'storages',
    'corsheaders',

    # Local apps
    'apps.user',
    'apps.vendors',
    'apps.design_requests',
    'apps.bids',
    'apps.orders',
    'apps.reviews',
    'apps.notifications',
    'apps.messaging',
    'apps.disputes',
    'apps.analytics',
]

MIDDLEWARE = [
    # CorsMiddleware must come first (before CommonMiddleware) so CORS headers
    # are added even on early responses/redirects.
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            # 'require' for Neon (default); set DB_SSLMODE=disable for a
            # local Postgres container that doesn't serve SSL.
            'sslmode': os.getenv('DB_SSLMODE', 'require'),
        },
    },
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'


# Default primary key field type
# https://docs.djangoproject.com/en/6.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Custom user model
AUTH_USER_MODEL = 'user.User'


# Authentication backends (allauth + Django default)
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1


# CORS
# Origins allowed to make cross-origin requests to the API (e.g. the frontend
# dev server). Extend via the comma-separated CORS_ALLOWED_ORIGINS env var.
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
]
_extra_cors = os.getenv('CORS_ALLOWED_ORIGINS', '')
if _extra_cors:
    CORS_ALLOWED_ORIGINS += [o.strip() for o in _extra_cors.split(',') if o.strip()]


# Django REST Framework
# Default to JWT auth, require authentication, and throttle by default.
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': os.getenv('THROTTLE_ANON', '30/min'),
        'user': os.getenv('THROTTLE_USER', '120/min'),
    },
}


# Simple JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}


# dj-rest-auth: issue JWTs (not DRF tokens) on login.
REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_HTTPONLY': False,
    # We issue JWTs, not DRF auth tokens, so disable the token model.
    'TOKEN_MODEL': None,
    'SESSION_LOGIN': False,
}


# allauth / social account configuration
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'

# Google OAuth2. Client id/secret come from Google Cloud Console and are read
# from the environment; the callback URL must match one registered there.
GOOGLE_OAUTH_CALLBACK_URL = os.getenv(
    'GOOGLE_OAUTH_CALLBACK_URL', 'http://localhost:8000/api/v1/user/auth/google/'
)
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.getenv('GOOGLE_OAUTH_CLIENT_ID', ''),
            'secret': os.getenv('GOOGLE_OAUTH_CLIENT_SECRET', ''),
            'key': '',
        },
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
    },
}


# Media & file storage
# Uploaded files (e.g. design images) go to S3 when AWS credentials are
# present in the environment; otherwise they fall back to local media so the
# project runs without any cloud setup in development.
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME')

_USE_S3 = bool(
    AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY and AWS_STORAGE_BUCKET_NAME
)

if _USE_S3:
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False
    _default_storage = {'BACKEND': 'storages.backends.s3.S3Storage'}
else:
    _default_storage = {'BACKEND': 'django.core.files.storage.FileSystemStorage'}

STORAGES = {
    'default': _default_storage,
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'
    },
}
