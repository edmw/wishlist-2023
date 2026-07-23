"""The webapp’s routes.

This is the starting of all url patterns. More url patterns of the other apps
are included here.
"""

from uuid import UUID

from allauth.account import views as allauth_account_views
from allauth.socialaccount import views as allauth_socialaccount_views
from django.conf import settings as django_settings
from django.contrib import admin
from django.urls import include, path, register_converter

from webapp.services import Base62Service

handler400 = "core.views.errors.bad_request"
handler403 = "core.views.errors.forbidden"
handler404 = "core.views.errors.not_found"
handler500 = "core.views.errors.internal_server_error"


class Base62UUIDConverter:
    """Converter to enable the use of base62-encoded UUIDs as path parameters.

    A path like this
    ```
    path("user/<b62uuid:pk>", ...)
    ```
    will expand into URLs like this
    ```
    http://<servername>/user/7f0KeLuI6kVdoHVD71MMDz
    ```
    where 7f0KeLuI6kVdoHVD71MMDz is the base62-encoded value of
    ```
    FBBA8FD5-8B70-4C3B-A33D-7E97BCD0D6FB
    ```
    """

    regex = "[0-9A-Za-z]{16,22}"

    def to_python(self, value: str) -> UUID:
        """Converts the specified string used in an url as path parameter
        by base62-decoding it.
        """
        return Base62Service.uuid_decode(base62_string=value)

    def to_url(self, value: UUID) -> str:
        """Converts the specified UUID for the use in an url as path parameter
        by base62-encoding it.
        """
        return Base62Service.uuid_encode(uuid=value)


register_converter(Base62UUIDConverter, "b62uuid")


urlpatterns = [
    # core
    path("", include("core.urls")),
    path(
        "-system/",
        include(
            [
                path("", include("core_health.urls")),
            ]
        ),
    ),
    # ALLAUTH
    # Include only selected patterns, because only the login via a social
    # accounts from allauth is used .
    path(
        "accounts/",
        include(
            [
                path("signup/", allauth_account_views.signup, name="account_signup"),
                path("login/", allauth_account_views.login, name="account_login"),
                path("logout/", allauth_account_views.logout, name="account_logout"),
                path("inactive/", allauth_account_views.account_inactive, name="account_inactive"),
                path(
                    "login/cancelled/",
                    allauth_socialaccount_views.login_cancelled,
                    name="socialaccount_login_cancelled",
                ),
                path("signup/", allauth_socialaccount_views.signup, name="socialaccount_signup"),
                path("", include("allauth.socialaccount.providers.google.urls")),
            ]
        ),
    ),
]

if django_settings.ADMIN_SITE_ENABLED:
    urlpatterns += [
        # Include admin site.
        path("admin/", admin.site.urls),
    ]

if "debug_toolbar" in django_settings.INSTALLED_APPS:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
