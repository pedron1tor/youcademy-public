import redis
from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
import os


MESSAGE_ = "django.contrib.messages.storage.session.SessionStorage"

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "pages",
    "teacher",
    "student",
    "channels",
    "classifier",
    "chat_interface",
    "rest_framework",
    "corsheaders",
    "api",
    "django_htmx",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.microsoft",
    "allauth.socialaccount.providers.google",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ]
}

ASGI_APPLICATION = "mainframe.asgi.application"

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "mainframe.middleware.DynamicHostMiddleware",
    "mainframe.middleware.NoWWWRedirectMiddleware",
    "mainframe.middleware.TimezoneMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://youcademy.dev",
    "http://127.0.0.1:8000",
    "https://storage.googleapis.com",
]

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^http://localhost:\d+$",  # Allow all localhost ports
]
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    "authorization",
    "content-type",
    "x-csrftoken",
    "x-requested-with",
]

CORS_ALLOW_METHODS = [
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS",
]

CORS_EXPOSE_HEADERS = [
    "Content-Type",
    "Authorization",
]

ROOT_URLCONF = "mainframe.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "pages.context_processors.custom_context",
                "django.template.context_processors.request",
            ],
        },
    },
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

WSGI_APPLICATION = "mainframe.wsgi.application"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 8,
        },
    },
]


INTERNAL_IPS = [
    # ...
    "127.0.0.1",
    # ...
]

LANGUAGE_CODE = "en"

LANGUAGES = [
    ("en", "English"),
    ("nl", "Dutch"),
]

CUSTOM_TRANSLATIONS_FILE = os.path.join(BASE_DIR, "utils/translations.json")

LOCALE_PATHS = [os.path.join(BASE_DIR, "locale")]

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGOUT_REDIRECT_URL = ""

AUTH_USER_MODEL = "pages.CustomUser"

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "APP": {
            "client_id": os.getenv("CLIENT_ID"),
            "secret": os.getenv("CLIENT_SECRET"),
        },
        "AUTH_PARAMS": {
            "access_type": "online",
        },
    },
    "microsoft": {
        "APPS": [
            {
                "client_id": os.getenv("MSFT_CLIENT_ID"),
                "secret": os.getenv("MSFT_SECRET"),
                "settings": {
                    "tenant": "organizations",
                },
            }
        ]
    },
}

LOGIN_URL = "/pages/login"
LOGIN_REDIRECT_URL = "/student/"
SOCIALACCOUNT_AUTO_SIGNUP = True
WS4REDIS_HEARTBEAT = "--heartbeat--"
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_ADAPTER = "mainframe.adapters.CustomSocialAccountAdapter"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_USERNAME_REQUIRED = None
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"

# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'verbose': {
#             'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
#             'style': '{',
#         },
#         'simple': {
#             'format': '{levelname} {message}',
#             'style': '{',
#         },
#     },
#     'handlers': {
#         'console': {
#             'level': 'DEBUG',
#             'class': 'logging.StreamHandler',
#             'formatter': 'simple',
#         },
#         'file': {
#             'level': 'DEBUG',
#             'class': 'logging.FileHandler',
#             'filename': os.path.join(BASE_DIR, 'debug.log'),
#             'formatter': 'verbose',
#         },
#     },
#     'loggers': {
#         '': {  # Root logger
#             'handlers': ['console', 'file'],
#             'level': 'DEBUG',
#         },
#         'django': {
#             'handlers': ['console', 'file'],
#             'level': 'INFO',
#             'propagate': False,
#         },
#         'allauth': {
#             'handlers': ['console', 'file'],
#             'level': 'DEBUG',
#             'propagate': False,
#         },
#     },
# }
