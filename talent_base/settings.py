"""
Django settings for talent_base project.
"""

import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = config("SECRET_KEY", default='django-insecure-fallback-key')
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    
    # Local apps
    'application_tracking',
    'accounts',
    'organization',  # ✅ Added Organization App
]

AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "/auth/login/"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # 'django.contrib.sessions.middleware.SessionMiddleware',
    'common.middleware.HostIsolatedSessionMiddleware', # ✅ Custom Isolated Session
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'talent_base.urls'

# ✅ UPDATED TEMPLATES CONFIGURATION
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
                
                # ✅ ADDED THIS LINE FOR NOTIFICATIONS:
                'application_tracking.context_processors.notification_counts',
            ],
        },
    },
]

WSGI_APPLICATION = 'talent_base.wsgi.application'

# ✅ DATABASE CONFIGURATION (PostgreSQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'kite_db',
        'USER': 'kite_user',
        'PASSWORD': 'Kite2058',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ✅ STATIC FILES
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# ✅ MEDIA SETTINGS
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =======================================================
# ✅ EMAIL CONFIGURATION (CONSOLE BACKEND FOR TESTING)
# =======================================================
# This setting forces Django to print emails to the Terminal window 
# instead of trying to send them via Gmail. This is crucial for local dev.
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Keep these settings in case you switch back to SMTP later
EMAIL_HOST = config("EMAIL_HOST", default='smtp.gmail.com')
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default='')
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default='')
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# CELERY CONFIG
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_SERIALIZER = "json"
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"

# ✅ KHALTI PAYMENT CONFIGURATION (SANDBOX)
KHALTI_SECRET_KEY = config("KHALTI_SECRET_KEY", default="")  # Sandbox Secret Key
KHALTI_INITIATE_URL = "https://dev.khalti.com/api/v2/epayment/initiate/"
KHALTI_LOOKUP_URL = "https://dev.khalti.com/api/v2/epayment/lookup/"
# This is where Khalti sends the user back after payment (Must match your urls.py)
KHALTI_RETURN_URL = "http://127.0.0.1:8000/org/payment/verify/"

# ✅ SITE URL FOR EMAIL LINKS
# Used in signals.py to generate the payment link
SITE_URL = "http://127.0.0.1:8000"

# ✅ GOOGLE GEMINI AI CONFIGURATION
GEMINI_API_KEY = config("GEMINI_API_KEY", default="")

# =======================================================
# ✅ CRITICAL FIX: CSRF TRUSTED ORIGINS
# =======================================================
# You MUST add this to prevent the "CSRF Failed: Origin checking failed" error
# This tells Django to trust requests coming from both localhost and 127.0.0.1
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

