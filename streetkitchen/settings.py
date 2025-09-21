"""
Django settings for streetkitchen project.
"""

from pathlib import Path
import os
import dj_database_url

# --------------------------
# Base Directory
# --------------------------
BASE_DIR = Path(__file__).resolve().parent.parent


# --------------------------
# Security
# --------------------------
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-()jhaofgb6h9psy4=kdj!i&+dl6x(3104p4lyi5f$15r^qd*@d"
)
DEBUG = os.getenv("DEBUG", "True") == "True"
ALLOWED_HOSTS = ["*"]  # ⚠️ For production, replace with Render domain


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
]


# --------------------------
# Middleware
# --------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # ✅ serves static files
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
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "krahul17@gmail.com")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "rgno ugxj splp iday")  # App Password
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

ADMINS = [
    ("Street Kitchen Admin", "foodsorder@gmail.com"),
]


# --------------------------
# Templates
# --------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
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
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
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
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True


# --------------------------
# Static Files
# --------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# --------------------------
# Media Files
# --------------------------
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# --------------------------
# Default Primary Key
# --------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
