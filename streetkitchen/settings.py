"""
Django settings for streetkitchen project.
"""

from pathlib import Path
import os

# --------------------------
# Base Directory
# --------------------------
BASE_DIR = Path(__file__).resolve().parent.parent


# --------------------------
# Security
# --------------------------
SECRET_KEY = "django-insecure-()jhaofgb6h9psy4=kdj!i&+dl6x(3104p4lyi5f$15r^qd*@d"
DEBUG = True
ALLOWED_HOSTS = ["*"]  # ⚠️ Allow all in dev; set explicit domains in production


# --------------------------
# Installed Apps
# --------------------------
INSTALLED_APPS = [
    # Django defaults
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Project apps
    "customers",
    "vendors",
    "menuitem",
    "orders",
    "streaming",
    "core",

    # Third-party (add as needed: crispy_forms, rest_framework, etc.)
]


# --------------------------
# Middleware
# --------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# --------------------------
# URL / WSGI
# --------------------------
ROOT_URLCONF = "streetkitchen.urls"
WSGI_APPLICATION = "streetkitchen.wsgi.application"

# --------------------------
# Email Configuration
# --------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "krahul17@gmail.com"        # replace with your Gmail
EMAIL_HOST_PASSWORD = "rgno ugxj splp iday"       # 🔑 use App Password (not your main Gmail password)

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Admin notifications
ADMINS = [
    ("Street Kitchen Admin", "foodsorder@gmail.com"),  # gets notified when new order is placed
]


# --------------------------
# Templates
# --------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # global templates folder
        "APP_DIRS": True,  # allow per-app templates
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",  # required for {% url %}
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# --------------------------
# Database
# --------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",  # ✅ use PostgreSQL in production
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# --------------------------
# Authentication
# --------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --------------------------
# Internationalization
# --------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"  # 🇮🇳 match your local timezone
USE_I18N = True
USE_TZ = True


# --------------------------
# Static Files
# --------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]  # global static folder
STATIC_ROOT = BASE_DIR / "staticfiles"  # collectstatic target


# --------------------------
# Media Files
# --------------------------
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_ROOT = BASE_DIR / "media"


# --------------------------
# Default Primary Key
# --------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
