"""The webapp’s applications settings."""

import email.utils
import functools
import logging
import re
from enum import StrEnum
from pathlib import Path
from urllib.parse import urljoin

import environs
import structlog
import structlog.types
from celery.schedules import crontab
from cryptography.fernet import Fernet
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest
from django.utils.csp import CSP
from marshmallow.validate import OneOf

from core.apps import CoreAccess, CoreConfig
from webapp import constants

env = environs.Env()

# Absolute path to the webapp’s base directory.
# Build paths inside the project like this: `BASE_DIR / "..."`.
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent


# region VERSION
###########################################################################################################
#
#  ##     ## ######## ########   ######  ####  #######  ##    ##
#  ##     ## ##       ##     ## ##    ##  ##  ##     ## ###   ##
#  ##     ## ##       ##     ## ##        ##  ##     ## ####  ##
#  ##     ## ######   ########   ######   ##  ##     ## ## ## ##
#   ##   ##  ##       ##   ##         ##  ##  ##     ## ##  ####
#    ## ##   ##       ##    ##  ##    ##  ##  ##     ## ##   ###
#     ###    ######## ##     ##  ######  ####  #######  ##    ##

version_file = Path("VERSION")
if version_file.is_file():
    with open(version_file) as f:
        VERSION = f.readline().strip()
else:
    VERSION = "development"

# endregion VERSION

# region ENVIRONMENT
###########################################################################################################
#
#  ######## ##    ## ##     ## #### ########   #######  ##    ## ##     ## ######## ##    ## ########
#  ##       ###   ## ##     ##  ##  ##     ## ##     ## ###   ## ###   ### ##       ###   ##    ##
#  ##       ####  ## ##     ##  ##  ##     ## ##     ## ####  ## #### #### ##       ####  ##    ##
#  ######   ## ## ## ##     ##  ##  ########  ##     ## ## ## ## ## ### ## ######   ## ## ##    ##
#  ##       ##  ####  ##   ##   ##  ##   ##   ##     ## ##  #### ##     ## ##       ##  ####    ##
#  ##       ##   ###   ## ##    ##  ##    ##  ##     ## ##   ### ##     ## ##       ##   ###    ##
#  ######## ##    ##    ###    #### ##     ##  #######  ##    ## ##     ## ######## ##    ##    ##


class Environment(StrEnum):
    """Enumerate all webapp’s environments."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    BUILDING = "building"


ENVIRONMENT = env.str(
    "WEBAPP_ENVIRONMENT",
    validate=OneOf(list(Environment), error="WEBAPP_ENVIRONMENT must be one of: {choices}"),
)

ENVIRONMENT_IS_DEVELOPMENT = ENVIRONMENT == Environment.DEVELOPMENT
ENVIRONMENT_IS_NOT_DEVELOPMENT = ENVIRONMENT != Environment.DEVELOPMENT
ENVIRONMENT_IS_TESTING = ENVIRONMENT == Environment.TESTING
ENVIRONMENT_IS_STAGING = ENVIRONMENT == Environment.STAGING
ENVIRONMENT_IS_PRODUCTION = ENVIRONMENT == Environment.PRODUCTION
ENVIRONMENT_IS_BUILDING = ENVIRONMENT == Environment.BUILDING

ENVIRONMENT_SUPPORTS_ADMIN = (
    ENVIRONMENT_IS_DEVELOPMENT or ENVIRONMENT_IS_STAGING or ENVIRONMENT_IS_PRODUCTION
)

DEBUG = env.bool("DJANGO_DEBUG", ENVIRONMENT == Environment.DEVELOPMENT)


# Helper to decrypt environment strings using the webapp’s secret key.
def env_decrpyt(key: str, default: str | None, fernet: Fernet | None) -> str | None:
    """Decrypts the environment string for the specified key using the
    specified cryptographic recipe.

    Returns the given default if no recipe is given or an environment string
    for the specified key does not exist.
    """
    if fernet:
        if value := env.str(key, None):
            return fernet.decrypt(value.encode("ascii")).decode("ascii")
    return default


# endregion ENVIRONMENT

# region WISHLIST
###########################################################################################################
#  ##      ## ####  ######  ##     ## ##       ####  ######  ########
#  ##  ##  ##  ##  ##    ## ##     ## ##        ##  ##    ##    ##
#  ##  ##  ##  ##  ##       ##     ## ##        ##  ##          ##
#  ##  ##  ##  ##   ######  ######### ##        ##   ######     ##
#  ##  ##  ##  ##        ## ##     ## ##        ##        ##    ##
#  ##  ##  ##  ##  ##    ## ##     ## ##        ##  ##    ##    ##
#   ###  ###  ####  ######  ##     ## ######## ####  ######     ##

WISH_IMAGE_PIXELS_MAX = 40_000_000

# endregion WISHLIST

# region DJANGO
###########################################################################################################
#
#  ########        ##    ###    ##    ##  ######    #######
#  ##     ##       ##   ## ##   ###   ## ##    ##  ##     ##
#  ##     ##       ##  ##   ##  ####  ## ##        ##     ##
#  ##     ##       ## ##     ## ## ## ## ##   #### ##     ##
#  ##     ## ##    ## ######### ##  #### ##    ##  ##     ##
#  ##     ## ##    ## ##     ## ##   ### ##    ##  ##     ##
#  ########   ######  ##     ## ##    ##  ######    #######

WEBAPP_KEY = Fernet(env.str("WEBAPP_KEY").encode("ascii")) if not ENVIRONMENT_IS_BUILDING else None
webapp_env_decrypt = functools.partial(env_decrpyt, fernet=WEBAPP_KEY)

WEBAPP_SCHEME = env.str("WEBAPP_SCHEME", "http")
WEBAPP_HOST = env.str("WEBAPP_HOST", "localhost")
WEBAPP_LOCATION = f"{WEBAPP_SCHEME}://{WEBAPP_HOST}"

ALLOWED_HOSTS = env.list("ALLOWED_HOST", ["localhost"])

ASGI_APPLICATION = "webapp.asgi.application"
WSGI_APPLICATION = "webapp.wsgi.application"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django_probes",
    "webapp.apps.WebappConfig",
    "webapp.apps.StaticFilesConfig",
    "webapp.apps.CeleryBeatConfig",
    "webapp.apps.CeleryResultsConfig",
    "core",
    "core_health",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "webapp.middlewares.request_middleware.request_middleware",
    "webapp.middlewares.logging_middleware.logging_middleware",
    "webapp.middlewares.language_middleware.language_middleware",
]

ROOT_URLCONF = "webapp.urls"

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# endregion DJANGO

# region DJANGO ADMIN
###########################################################################################################
#
#  ########        ##    ###    ##    ##  ######    #######        ###    ########  ##     ## #### ##    ##
#  ##     ##       ##   ## ##   ###   ## ##    ##  ##     ##      ## ##   ##     ## ###   ###  ##  ###   ##
#  ##     ##       ##  ##   ##  ####  ## ##        ##     ##     ##   ##  ##     ## #### ####  ##  ####  ##
#  ##     ##       ## ##     ## ## ## ## ##   #### ##     ##    ##     ## ##     ## ## ### ##  ##  ## ## ##
#  ##     ## ##    ## ######### ##  #### ##    ##  ##     ##    ######### ##     ## ##     ##  ##  ##  ####
#  ##     ## ##    ## ##     ## ##   ### ##    ##  ##     ##    ##     ## ##     ## ##     ##  ##  ##   ###
#  ########   ######  ##     ## ##    ##  ######    #######     ##     ## ########  ##     ## #### ##    ##

ADMIN_SITE_ENABLED = env.bool("WEBAPP_ADMIN_SITE_ENABLED", False)

ADMIN_SITE_APPS = {
    # "app_name": <sorting_index>,
    "core": 0,  # move to top (lowest index)
    "core_health": 10,
    "account": 50,
    "socialaccount": 51,
    "auth": 60,
    "django_celery_beat": 100,
    "django_celery_results": 101,
    "waffle": 900,  # move to bottom (highest index)
    # defaults to 1, entries with the same index are sorted alphabetically
}

# Allow admin site on localhost only.
if ADMIN_SITE_ENABLED:
    ADMIN_ALLOWED_HOST_REGEXES = [
        r"localhost$",
    ]
    for host in ALLOWED_HOSTS:
        if any(re.match(host_regex, host) for host_regex in ADMIN_ALLOWED_HOST_REGEXES):
            continue
        raise ImproperlyConfigured(
            f"Admin site is enabled and ALLOWED_HOST ({ALLOWED_HOSTS}) "
            f"contains a domain which matches none of these regexes: "
            f"{ADMIN_ALLOWED_HOST_REGEXES}"
        )

# Install admin site.
if ADMIN_SITE_ENABLED:
    INSTALLED_APPS.append("webapp.admin.WebappAdminConfig")

# endregion DJANGO ADMIN

# region DJANGO API
#####################################################################################################
#
#  ########        ##    ###    ##    ##  ######    #######        ###    ########  ####
#  ##     ##       ##   ## ##   ###   ## ##    ##  ##     ##      ## ##   ##     ##  ##
#  ##     ##       ##  ##   ##  ####  ## ##        ##     ##     ##   ##  ##     ##  ##
#  ##     ##       ## ##     ## ## ## ## ##   #### ##     ##    ##     ## ########   ##
#  ##     ## ##    ## ######### ##  #### ##    ##  ##     ##    ######### ##         ##
#  ##     ## ##    ## ##     ## ##   ### ##    ##  ##     ##    ##     ## ##         ##
#  ########   ######  ##     ## ##    ##  ######    #######     ##     ## ##        ####

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "EXCEPTION_HANDLER": "webapp.api.exception_handler",
}

# endregion DJANGO API

# region SECURITY
###########################################################################################################
#
#   ######  ########  ######  ##     ## ########  #### ######## ##    ##
#  ##    ## ##       ##    ## ##     ## ##     ##  ##     ##     ##  ##
#  ##       ##       ##       ##     ## ##     ##  ##     ##      ####
#   ######  ######   ##       ##     ## ########   ##     ##       ##
#        ## ##       ##       ##     ## ##   ##    ##     ##       ##
#  ##    ## ##       ##    ## ##     ## ##    ##   ##     ##       ##
#   ######  ########  ######   #######  ##     ## ####    ##       ##

# Secret key used to provide cryptographic signing.
# WARNING: keep the value used in production secret!
SECRET_KEY = env.str("SECRET_KEY", "secret")

# Accept HTTP Forwarded Header if running locally.
# WARNING: neither needed for production nor recommended!
SECURE_PROXY_SSL_HEADER = (
    None if ENVIRONMENT != ENVIRONMENT_IS_DEVELOPMENT else ("HTTP_X_FORWARDED_PROTO", "https")
)

SESSION_COOKIE_SECURE = ENVIRONMENT_IS_NOT_DEVELOPMENT
SESSION_COOKIE_AGE = 36000  # 10 hours in seconds
SESSION_COOKIE_NAME = "sessionid"
SESSION_COOKIE_PATH = "/"
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_HTTPONLY = True
SESSION_ENGINE = "django.contrib.sessions.backends.db"

CSRF_COOKIE_SECURE = ENVIRONMENT_IS_NOT_DEVELOPMENT
CSRF_COOKIE_AGE = 31449600  # 1 year in seconds
CSRF_COOKIE_NAME = "csrftoken"
CSRF_COOKIE_PATH = "/"
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False
CSRF_HEADER_NAME = "HTTP_X_CSRFTOKEN"
CSRF_TRUSTED_ORIGINS = [WEBAPP_LOCATION]

SECURE_CSP = {
    "default-src": [CSP.SELF],
    "style-src": [CSP.SELF, CSP.NONCE],
    "script-src": [CSP.SELF, CSP.NONCE],
    "img-src": [CSP.SELF, "data:"],
}

# endregion SECURITY

# region AUTH
###########################################################################################################
#
#     ###    ##     ## ######## ##     ##
#    ## ##   ##     ##    ##    ##     ##
#   ##   ##  ##     ##    ##    ##     ##
#  ##     ## ##     ##    ##    #########
#  ######### ##     ##    ##    ##     ##
#  ##     ## ##     ##    ##    ##     ##
#  ##     ##  #######     ##    ##     ##

AUTH_USER_MODEL = "core.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LOGIN_REDIRECT_URL = "start"
LOGOUT_REDIRECT_URL = "start"

AUTHENTICATION_BACKENDS = [
    "allauth.account.auth_backends.AuthenticationBackend",
]
if ADMIN_SITE_ENABLED:
    AUTHENTICATION_BACKENDS.insert(0, "django.contrib.auth.backends.ModelBackend")

ACCOUNT_ADAPTER = "webapp.authenticator.WebappAccountAdapter"
ACCOUNT_SIGNUP_FIELDS = ["email*", "username*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_USERNAME_BLACKLIST = [
    "root",
    "super",
    "admin",
    "administrator",
    "administration",
    "abuse",
    "mail",
    "info",
]

SOCIALACCOUNT_ADAPTER = "webapp.authenticator.WebappSocialAccountAdapter"
SOCIALACCOUNT_PROVIDERS = {}

if not ENVIRONMENT_IS_BUILDING:
    SOCIALACCOUNT_PROVIDERS["google"] = {
        "APP": {
            "client_id": env.str("AUTH_GOOGLE_CLIENT_ID"),
            "secret": webapp_env_decrypt("AUTH_GOOGLE_SECRET", ""),
        },
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
        "OAUTH_PKCE_ENABLED": True,
    }

SOCIALACCOUNT_AUTO_SIGNUP = CoreConfig.access == CoreAccess.PUBLIC

# endregion AUTH

# region STATIC
#################################################################################################
#
#   ######  ########    ###    ######## ####  ######
#  ##    ##    ##      ## ##      ##     ##  ##    ##
#  ##          ##     ##   ##     ##     ##  ##
#   ######     ##    ##     ##    ##     ##  ##
#        ##    ##    #########    ##     ##  ##
#  ##    ##    ##    ##     ##    ##     ##  ##    ##
#   ######     ##    ##     ##    ##    ####  ######

STATIC_URL = "static/"

STATIC_ROOT = "/webapp-static"

STATICFILES_DIRS = [
    ("core", BASE_DIR / "core" / "frontend"),
    ("webapp", BASE_DIR / "webapp" / "frontend"),
    ("vendor", "/build/dist/"),
]

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

if (
    (ENVIRONMENT_IS_DEVELOPMENT and not DEBUG)
    or ENVIRONMENT_IS_BUILDING
    or ENVIRONMENT_IS_STAGING
    or ENVIRONMENT_IS_PRODUCTION
):
    # apply cache busting with content hashes
    STORAGES["staticfiles"]["BACKEND"] = "whitenoise.storage.CompressedManifestStaticFilesStorage"
    WHITENOISE_KEEP_ONLY_HASHED_FILES = True

WHITENOISE_ROOT = BASE_DIR / "webapp" / "frontend" / "root"

# endregion STATIC

# region MEDIA
###########################################################################################################
#
#  ##     ## ######## ########  ####    ###
#  ###   ### ##       ##     ##  ##    ## ##
#  #### #### ##       ##     ##  ##   ##   ##
#  ## ### ## ######   ##     ##  ##  ##     ##
#  ##     ## ##       ##     ##  ##  #########
#  ##     ## ##       ##     ##  ##  ##     ##
#  ##     ## ######## ########  #### ##     ##

with env.prefixed("WEBAPP_MEDIA_"):
    WEBAPP_MEDIA_HOST = env.str("HOST", "localhost")
    WEBAPP_MEDIA_LOCATION = f"{WEBAPP_SCHEME}://{WEBAPP_MEDIA_HOST}"
    WEBAPP_MEDIA_PATH = env.str("PATH", "/media")
    WEBAPP_MEDIA_URL = urljoin(WEBAPP_MEDIA_LOCATION, WEBAPP_MEDIA_PATH)

AWS_S3_URL_PROTOCOL = f"{WEBAPP_SCHEME}:"
AWS_S3_CUSTOM_DOMAIN = f"{WEBAPP_MEDIA_HOST}{WEBAPP_MEDIA_PATH}"

with env.prefixed("STORAGE_"):
    AWS_S3_ENDPOINT_URL = env.str("URL", None)
    AWS_ACCESS_KEY_ID = env.str("ACCESS_KEY", None)
    AWS_STORAGE_BUCKET_NAME = env.str("BUCKET_FILES", "wishlist")
    AWS_S3_REGION_NAME = env.str("REGION", "us-east-1")
    AWS_S3_ADDRESSING_STYLE = env.str("ADDRESSING_STYLE", "path")
    AWS_S3_SIGNATURE_VERSION = env.str("SIGNATURE_VERSION", "s3v4")

AWS_SECRET_ACCESS_KEY = webapp_env_decrypt("STORAGE_SECRET_KEY", None)

SECURE_CSP["img-src"] = [
    *SECURE_CSP["img-src"],
    WEBAPP_MEDIA_LOCATION,
]

# endregion MEDIA

# region I18N
#####################################################################################################
#
#  ####    ##    #######  ##    ##
#   ##   ####   ##     ## ###   ##
#   ##     ##   ##     ## ####  ##
#   ##     ##    #######  ## ## ##
#   ##     ##   ##     ## ##  ####
#   ##     ##   ##     ## ##   ###
#  ####  ######  #######  ##    ##

USE_I18N = True

LANGUAGES = [
    ("en", "English"),
    ("de", "German"),
]

LANGUAGE_CODE = "en"

LANGUAGE_COOKIE_NAME = "language"
LANGUAGE_COOKIE_HTTPONLY = True
LANGUAGE_COOKIE_SAMESITE = "Strict"

LOCALE_PATHS = [
    BASE_DIR / "webapp" / "locale",
    BASE_DIR / "core" / "locale",
]

FORMAT_MODULE_PATH = [
    "core.locale",
]
FORMAT_DATETIME = {
    "en": "%m/%d/%Y at %I:%M %p",
    "de": "%d.%m.%Y um %H:%M Uhr",
}

USE_TZ = True

TIME_ZONE = "Europe/Berlin"

# endregion I18N

# region TEMPLATES
#################################################################################################
#
#  ######## ######## ##     ## ########  ##          ###    ######## ########  ######
#     ##    ##       ###   ### ##     ## ##         ## ##      ##    ##       ##    ##
#     ##    ##       #### #### ##     ## ##        ##   ##     ##    ##       ##
#     ##    ######   ## ### ## ########  ##       ##     ##    ##    ######    ######
#     ##    ##       ##     ## ##        ##       #########    ##    ##             ##
#     ##    ##       ##     ## ##        ##       ##     ##    ##    ##       ##    ##
#     ##    ######## ##     ## ##        ######## ##     ##    ##    ########  ######

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["core/views"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.csp",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "webapp.views.context.settings",
                "core.views.context.settings",
                "core.views.context.constants",
            ],
            "libraries": {
                "core": "core.templates_tags",
            },
        },
    },
]

# endregion TEMPLATES

# region SERVICES
###########################################################################################################
#
#   ######  ######## ########  ##     ## ####  ######  ########  ######
#  ##    ## ##       ##     ## ##     ##  ##  ##    ## ##       ##    ##
#  ##       ##       ##     ## ##     ##  ##  ##       ##       ##
#   ######  ######   ########  ##     ##  ##  ##       ######    ######
#        ## ##       ##   ##    ##   ##   ##  ##       ##             ##
#  ##    ## ##       ##    ##    ## ##    ##  ##    ## ##       ##    ##
#   ######  ######## ##     ##    ###    ####  ######  ########  ######

with env.prefixed("PUSHOVER_"):
    PUSHOVER_SERVICE_URL = env.str("SERVICE_URL", None)
    PUSHOVER_CONNECT_TIMEOUT_MS = env.int("CONNECT_TIMEOUT_MS", 1000)
    PUSHOVER_READ_TIMEOUT_MS = env.int("READ_TIMEOUT_MS", 3000)

PUSHOVER_APPLICATION_TOKEN = webapp_env_decrypt("PUSHOVER_APPLICATION_TOKEN", None)

# endregion SERVICES

# region DATABASE
###########################################################################################################
#
#  ########     ###    ########    ###    ########     ###     ######  ########
#  ##     ##   ## ##      ##      ## ##   ##     ##   ## ##   ##    ## ##
#  ##     ##  ##   ##     ##     ##   ##  ##     ##  ##   ##  ##       ##
#  ##     ## ##     ##    ##    ##     ## ########  ##     ##  ######  ######
#  ##     ## #########    ##    ######### ##     ## #########       ## ##
#  ##     ## ##     ##    ##    ##     ## ##     ## ##     ## ##    ## ##
#  ########  ##     ##    ##    ##     ## ########  ##     ##  ######  ########

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env.str("DATABASE_NAME", "postgres"),
        "HOST": env.str("DATABASE_HOST", "localhost"),
        "PORT": env.str("DATABASE_PORT", "5432"),
        "USER": env.str("DATABASE_USER", "postgres"),
        "PASSWORD": webapp_env_decrypt("DATABASE_PASSWORD", ""),
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CONN_MAX_AGE = 600 if not ENVIRONMENT_IS_DEVELOPMENT else 0

# endregion DATABASE

# region CACHING
#####################################################################################################
#
#   ######     ###     ######  ##     ## #### ##    ##  ######
#  ##    ##   ## ##   ##    ## ##     ##  ##  ###   ## ##    ##
#  ##        ##   ##  ##       ##     ##  ##  ####  ## ##
#  ##       ##     ## ##       #########  ##  ## ## ## ##   ####
#  ##       ######### ##       ##     ##  ##  ##  #### ##    ##
#  ##    ## ##     ## ##    ## ##     ##  ##  ##   ### ##    ##
#   ######  ##     ##  ######  ##     ## #### ##    ##  ######

CACHE_BACKEND = env.str("CACHE_BACKEND", None)
CACHE_LOCATION = env.str("CACHE_LOCATION", None)

CACHE = {
    "BACKEND": CACHE_BACKEND,
    "LOCATION": CACHE_LOCATION,
    "OPTIONS": {},
    "KEY_PREFIX": env.str("CACHE_KEY_PREFIX", None),
}

if CACHE_PASSWORD := env.str("CACHE_PASSWORD", None):
    CACHE["OPTIONS"]["PASSWORD"] = CACHE_PASSWORD

CACHES = {"default": CACHE}

if ENVIRONMENT_IS_TESTING:
    # see WAFFLE settings above
    CACHES["dummy"] = {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}

# endregion CACHING

# region TASKING
#####################################################################################################
#
#  ########    ###     ######  ##    ## #### ##    ##  ######
#     ##      ## ##   ##    ## ##   ##   ##  ###   ## ##    ##
#     ##     ##   ##  ##       ##  ##    ##  ####  ## ##
#     ##    ##     ##  ######  #####     ##  ## ## ## ##   ####
#     ##    #########       ## ##  ##    ##  ##  #### ##    ##
#     ##    ##     ## ##    ## ##   ##   ##  ##   ### ##    ##
#     ##    ##     ##  ######  ##    ## #### ##    ##  ######

CELERY_TIMEZONE = "Europe/Berlin"
CELERY_BROKER_URL = env.str("CELERY_BROKER_URL", None)
if CELERY_BROKER_URL and CELERY_BROKER_URL.startswith("rediss://"):
    CELERY_BROKER_USE_SSL = {
        "ssl_cert_reqs": "required",
        "ssl_ca_certs": env.str("CELERY_BROKER_CA_CERTS", None),
    }
else:
    CELERY_BROKER_USE_SSL = None

CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_DEFAULT_QUEUE = env.str("CELERY_TASK_QUEUE", "de.yamanote.wl")
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_BACKEND = "django-db"
CELERY_RESULT_SERIALIZER = "json"
CELERY_RESULT_EXTENDED = True
CELERY_RESULT_EXPIRES = 10 * 86400  # 10 days
CELERY_WORKER_HIJACK_ROOT_LOGGER = False

CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_BEAT_SCHEDULE = {
    "webapp.sessions_cleanup": {
        "task": "webapp.sessions_cleanup",
        "schedule": crontab(hour="*/1", minute="17"),  # “At minute 17 past every hour.”
    },
}

CELERYD_LOG_COLOR = False
CELERYD_REDIRECT_STDOUTS = False

# endregion TASKING

# region EMAIL
###########################################################################################################
#
#  ######## ##     ##    ###    #### ##
#  ##       ###   ###   ## ##    ##  ##
#  ##       #### ####  ##   ##   ##  ##
#  ######   ## ### ## ##     ##  ##  ##
#  ##       ##     ## #########  ##  ##
#  ##       ##     ## ##     ##  ##  ##
#  ######## ##     ## ##     ## #### ########


with env.prefixed("EMAIL_"):
    EMAIL_BACKEND = env.str("BACKEND", "django.core.mail.backends.smtp.EmailBackend")
    EMAIL_HOST = env.str("SMTP_HOSTNAME", "localhost")
    EMAIL_HOST_USER = env.str("SMTP_USERNAME", "")
    EMAIL_USE_TLS = True

    EMAIL_SENDER_ADDRESS = env.str("SENDER_ADDRESS", "")
    EMAIL_SENDER_NAME = env.str("SENDER_NAME", "")
    EMAIL_SENDER = email.utils.formataddr((EMAIL_SENDER_NAME, EMAIL_SENDER_ADDRESS))

EMAIL_HOST_PASSWORD = webapp_env_decrypt("EMAIL_SMTP_PASSWORD", "")

EMAIL_SUBJECT_PREFIX = f"[{EMAIL_SENDER_NAME}] "

# endregion MAIL

# region LOGGING
#####################################################################################################
#
#  ##        #######   ######    ######   #### ##    ##  ######
#  ##       ##     ## ##    ##  ##    ##   ##  ###   ## ##    ##
#  ##       ##     ## ##        ##         ##  ####  ## ##
#  ##       ##     ## ##   #### ##   ####  ##  ## ## ## ##   ####
#  ##       ##     ## ##    ##  ##    ##   ##  ##  #### ##    ##
#  ##       ##     ## ##    ##  ##    ##   ##  ##   ### ##    ##
#  ########  #######   ######    ######   #### ##    ##  ######


class ProjectMetaAdder:
    """Log event processor to add project meta data."""

    def __init__(self, project_component: str, project_name: str | None = None):
        """Initializes the processor with project meta data."""
        self.project_name = project_name or CoreConfig.verbose_name.upper()
        self.project_component = project_component

    def __call__(
        self, logger: logging.Logger, name: str, event_dict: structlog.types.EventDict
    ) -> structlog.types.EventDict:
        """Adds project meta data."""
        event_dict["meta.project.name"] = self.project_name
        event_dict["meta.project.component"] = self.project_component
        return event_dict


class RequestExpander:
    """Log event processor to expand request objects to single plain fields."""

    def __call__(
        self, logger: logging.Logger, name: str, event_dict: structlog.types.EventDict
    ) -> structlog.types.EventDict:
        """Expands request objects to single plain fields."""
        if "request" in event_dict:
            request = event_dict.pop("request")
            if isinstance(request, HttpRequest):
                event_dict["http.request.method"] = request.method
                event_dict["http.request.path"] = request.path
                if request.resolver_match:
                    event_dict["django.view.name"] = request.resolver_match.view_name
        if "request_id" in event_dict:
            request_id = event_dict.pop("request_id")
            event_dict["http.request.id"] = request_id
        return event_dict


class KeyRenamer:
    """Log event processor to rename keys according to the Structured Logging Standard.

    Also renames the "event" key to "log.message" (must be last processor before renderer).
    """

    def __init__(self, keep_logging: bool = False):
        """Initializes a KeyRenamer.

        Keyword Arguments:
            keep_logging -- Do not remove logging-relevant keys. This is
                important if the log renderer depends on these keys.
                (default: {False})
        """
        self.keep_logging = keep_logging

    def _rename(
        self, event_dict: structlog.types.EventDict, key_name: str, key_name_new: str, keep: bool = False
    ) -> None:
        """Renames the specified key, if it exists, to the given new key name,
        does nothing otherwise.

        Arguments:
            event_dict -- Event dictionary with event keys and values.
            key_name -- Name of the key to rename.
            key_name_new -- New name for the key to be renamed.

        Keyword Arguments:
            keep -- Keep the key after renaming. (default: {False})
        """
        if key_name in event_dict:
            if keep:
                event = event_dict.get(key_name)
            else:
                event = event_dict.pop(key_name)
            event_dict[key_name_new] = event

    def __call__(
        self, logger: logging.Logger, name: str, event_dict: structlog.types.EventDict
    ) -> structlog.types.EventDict:
        self._rename(event_dict, "timestamp", "@timestamp", keep=self.keep_logging)
        self._rename(event_dict, "level", constants.LOG_LEVEL_KEY, keep=self.keep_logging)
        self._rename(event_dict, "logger", constants.LOG_NAME_KEY, keep=self.keep_logging)
        self._rename(event_dict, "event", constants.LOG_MESSAGE_KEY)
        self._rename(event_dict, "filename", constants.LOG_FILE_NAME_KEY)
        self._rename(event_dict, "lineno", constants.LOG_FILE_LINE_KEY)
        self._rename(event_dict, "func_name", constants.LOG_FUNCTION_KEY)
        self._rename(event_dict, "status_code", constants.LOG_HTTP_RESPONSE_STATUS_CODE_KEY)
        self._rename(event_dict, "server_time", constants.LOG_DJANGO_SERVER_TIME_KEY)
        return event_dict


structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)


STRUCTLOG_FOREIGN_PRE_CHAIN = [
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.stdlib.ExtraAdder(),
]


if ENVIRONMENT_IS_DEVELOPMENT:
    STRUCTLOG_PROCESSORS = [
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.CallsiteParameterAdder(
            {
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            }
        ),
        RequestExpander(),
        KeyRenamer(keep_logging=True),
        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
        structlog.dev.ConsoleRenderer(event_key=constants.LOG_MESSAGE_KEY, pad_event=0),
    ]
else:
    STRUCTLOG_PROCESSORS = [
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.ExceptionRenderer(
            exception_formatter=structlog.tracebacks.ExceptionDictTransformer()
        ),
        structlog.processors.CallsiteParameterAdder(
            {
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            }
        ),
        RequestExpander(),
        KeyRenamer(),
        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
        structlog.processors.JSONRenderer(sort_keys=True),
    ]


LOGGING_HANDLER_CLASS = "logging.StreamHandler"

LOGGING_LEVEL = "DEBUG" if DEBUG else "WARNING"
LOGGING_LEVEL_SHALLOW = "INFO" if DEBUG else "WARNING"
LOGGING_LEVEL_WARNING = "WARNING"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[core] {levelname} {asctime} {module} {name}.{funcName}:{lineno}: {message}",
            "style": "{",
        },
        "formatter_core": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processors": [
                ProjectMetaAdder(project_component=CoreConfig.name.lower()),
            ]
            + STRUCTLOG_PROCESSORS,
            "foreign_pre_chain": STRUCTLOG_FOREIGN_PRE_CHAIN,
        },
        "formatter_celery": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processors": [
                ProjectMetaAdder(project_component="celery"),
            ]
            + STRUCTLOG_PROCESSORS,
            "foreign_pre_chain": STRUCTLOG_FOREIGN_PRE_CHAIN,
        },
        "formatter_celery_task": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processors": [
                ProjectMetaAdder(project_component="celery/worker"),
            ]
            + STRUCTLOG_PROCESSORS,
            "foreign_pre_chain": STRUCTLOG_FOREIGN_PRE_CHAIN,
        },
    },
    "handlers": {
        "console": {
            "class": LOGGING_HANDLER_CLASS,
            "formatter": "formatter_core",
        },
        "console_celery": {
            "class": LOGGING_HANDLER_CLASS,
            "formatter": "formatter_celery",
        },
        "console_celery_task": {
            "class": LOGGING_HANDLER_CLASS,
            "formatter": "formatter_celery_task",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOGGING_LEVEL_WARNING,
    },
    "loggers": {
        "webapp": {
            "level": LOGGING_LEVEL,
        },
        "core": {
            "level": LOGGING_LEVEL,
        },
        "core.api": {
            "level": LOGGING_LEVEL,
        },
        "django": {
            "level": LOGGING_LEVEL,
        },
        "django.server": {
            "level": LOGGING_LEVEL,
        },
        "django.db.backends": {
            "level": LOGGING_LEVEL_SHALLOW,
        },
        "django.utils.autoreload": {
            "level": LOGGING_LEVEL_SHALLOW,
        },
        "celery": {  # celery logging: used by celery components
            "handlers": ["console_celery"],
            "level": LOGGING_LEVEL_WARNING,
            "propagate": False,
        },
        "celery.task": {  # celery task logging: used by application tasks
            "handlers": ["console_celery_task"],
            "level": LOGGING_LEVEL,
            "propagate": False,
        },
    },
}

# endregion LOGGING

# region DEBUGGING
#####################################################################################################
#
#  ########  ######## ########  ##     ##  ######    ######   #### ##    ##  ######
#  ##     ## ##       ##     ## ##     ## ##    ##  ##    ##   ##  ###   ## ##    ##
#  ##     ## ##       ##     ## ##     ## ##        ##         ##  ####  ## ##
#  ##     ## ######   ########  ##     ## ##   #### ##   ####  ##  ## ## ## ##   ####
#  ##     ## ##       ##     ## ##     ## ##    ##  ##    ##   ##  ##  #### ##    ##
#  ##     ## ##       ##     ## ##     ## ##    ##  ##    ##   ##  ##   ### ##    ##
#  ########  ######## ########   #######   ######    ######   #### ##    ##  ######

if ENVIRONMENT_IS_DEVELOPMENT or ENVIRONMENT_IS_STAGING:
    INSTALLED_APPS += [
        "debug_toolbar",
    ]

    MIDDLEWARE += [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
    ]

    DEBUG_TOOLBAR_PANELS = [
        "debug_toolbar.panels.versions.VersionsPanel",
        "debug_toolbar.panels.timer.TimerPanel",
        "debug_toolbar.panels.settings.SettingsPanel",
        "debug_toolbar.panels.headers.HeadersPanel",
        "debug_toolbar.panels.request.RequestPanel",
        "debug_toolbar.panels.sql.SQLPanel",
        "debug_toolbar.panels.staticfiles.StaticFilesPanel",
        "debug_toolbar.panels.templates.TemplatesPanel",
        "debug_toolbar.panels.cache.CachePanel",
        "debug_toolbar.panels.signals.SignalsPanel",
        "debug_toolbar.panels.redirects.RedirectsPanel",
        "debug_toolbar.panels.profiling.ProfilingPanel",
    ]

    def debug_toolbar_show(request: HttpRequest) -> bool:
        """Returns true, if debug toolbar should show.

        Add request query parameter "debug=true" to enable debug toolbar.
        """
        key = "debug"
        return (key in request.GET and request.GET[key] == "true") or "__debug__" in request.path

    DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": debug_toolbar_show}

# endregion DEBUGGING
