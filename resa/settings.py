"""
Django settings for resa project.

Generated by 'django-admin startproject' using Django 1.10.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import ast
import os

import dj_database_url
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# DEBUG ?
# Retrieve environment
ENV = os.getenv('DJANGO_ENV', 'prod')
debug_env = os.getenv('DEBUG', None)

# Define production
PROD = ENV in ['prod', 'production']

# By default, if we're in prod, we don't want debug
DEBUG = not PROD

# But we can override this.
if debug_env is not None:
    DEBUG = ast.literal_eval(debug_env)

# SSL will be required if in prod, unless the SSL is set to False.
ssl_required = PROD and ast.literal_eval(os.getenv('SSL', 'True'))

SECURE_BROWSER_XSS_FILTER = ssl_required
SECURE_CONTENT_TYPE_NOSNIFF = ssl_required
SESSION_COOKIE_SECURE = ssl_required
CSRF_COOKIE_SECURE = ssl_required
CSRF_COOKIE_HTTPONLY = PROD
USE_X_FORWARDED_HOST = PROD
SECURE_SSL_REDIRECT = ssl_required

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'r6=0@#g#py60s2ujq=03^^w^8*mh_!a7wpou_fu7&&40p3r+(o'

ALLOWED_HOSTS = ['localhost', '.herokuapp.com']


# Application definition

INSTALLED_APPS = [
    'authentication',
    'crispy_forms',
    'autofixture',
    'bookings',
    'bootstrap3_datetime',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'resa.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'bookings.processors.resource_and_category_list',
            ],
        },
    },
]

WSGI_APPLICATION = 'resa.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

db_from_env = dj_database_url.config(conn_max_age=500)
DATABASES['default'].update(db_from_env)


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = os.getenv('DJANGO_LOCALE', 'en-us')

TIME_ZONE = os.getenv('DJANGO_TIMEZONE', 'UTC')

USE_I18N = True

USE_L10N = True

USE_TZ = False

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

LANGUAGES = [
    ('fr', _('French')),
    ('en', _('English')),
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# Extra places for collectstatic to find static files.
STATICFILES_DIRS = (
    # os.path.join(BASE_DIR, 'codes', 'static'),
    'static',
)

STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'

# Media files (uploaded by users)
MEDIA_ROOT = os.path.join(BASE_DIR, 'uploads')
MEDIA_URL = '/uploads/'

LOGIN_URL = 'auth:login'
LOGOUT_URL = 'auth:logout'
LOGIN_REDIRECT_URL = 'bookings:home'
LOGOUT_REDIRECT_URL = 'bookings:home'

CRISPY_TEMPLATE_PACK = 'bootstrap3'

MESSAGE_TAGS = {
    messages.ERROR: 'danger'
}
