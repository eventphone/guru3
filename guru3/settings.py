"""
Django settings for guru3 project.

Generated by 'django-admin startproject' using Django 2.0.1.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os
import guru3.hardening

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Application definition

INSTALLED_APPS = [
    'dal',
    'dal_select2',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_bootstrap4',
    'django_registration',
    'core',
    'gcontrib',
    'grandstream',
    'snom',
    'epddi',
    'captcha',
    'channels',
    'wkhtmltopdf',
    'fontawesomefree',
]
CAPTCHA_CHALLENGE_FUNCT = 'captcha.helpers.math_challenge'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.apikey.ApiKeyAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

SECURE_CONTENT_TYPE_NOSNIFF = True

ROOT_URLCONF = 'guru3.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, "templates")],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.template_processors.events_processor'
            ],
        },
    },
]

WSGI_APPLICATION = 'guru3.wsgi.application'
ASGI_APPLICATION = 'guru3.routing.application'

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

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

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'guru3.hashers.Guru2PasswordHasher'
]

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = False

USE_TZ = False

# Improve security on cookies
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True

SESSION_COOKIE_SECURE = True

LOGIN_REDIRECT_URL = "/"
AUTH_KEY_HEADER = "ApiKey"

# Date format
DATE_FORMAT = "d.m.Y"
DATE_INPUT_FORMATS = ['%d.%m.%y', '%d.%m.%Y']

# Accounts settings
LOGOUT_REDIRECT_URL = "/"

# Crispy forms options
CRISPY_TEMPLATE_PACK = 'bootstrap4'

# Registration options
ACCOUNT_ACTIVATION_DAYS = 30

# Fixture information
PERMANENT_EVENT_ID = "1"
PERMANENT_PUBLIC_EVENT_ID = "2"

from guru3.local_settings import *
