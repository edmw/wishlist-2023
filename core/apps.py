"""The Core’s application configuration."""

import datetime
import zoneinfo
from enum import StrEnum
from typing import Optional

import environs
from django.apps import AppConfig
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _


class CoreAccess(StrEnum):
    PUBLIC = "public"
    EXISTING = "existing"
    NOBODY = "nobody"


class CoreConfig(AppConfig):
    """Core application configuration."""

    RELEASE_1_DATE = datetime.datetime(2222, 1, 1, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("CET"))

    # FEATURE FLAGS & SWITCHES

    # APP

    name = "core"
    verbose_name = "Wishlist"
    description = (
        "Wishlist is a web application for managing wish lists. "
        "It allows users to create lists of items they want most "
        "and share them with others."
    )

    access = CoreAccess.EXISTING

    contact_name: Optional[str]
    contact_address: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]

    # SIGNALS & TASKS

    def ready(self) -> None:
        """Initializes the Core application:
        Called once when the application has become ready.
        """
        import core.signals.allauth
        import core.tasks.wish

        env = environs.Env()
        with env.prefixed("CORE_"):
            CoreConfig.contact_name = env.str("CONTACT_NAME", None)
            CoreConfig.contact_address = env.str("CONTACT_ADDRESS", None)
            CoreConfig.contact_email = env.str("CONTACT_EMAIL", None)
            CoreConfig.contact_phone = env.str("CONTACT_PHONE", None)

    # BEHAVIOUR

    @staticmethod
    def authentiction_error_response(*, request: HttpRequest) -> HttpResponse | None:
        """Returns a redirect response to the start page if an authentication
        error occurred. Adds an error message to the response.

        NOTE: This function is utilized by `webapp.authenticator`.
        """
        request_id = getattr(request, "request_id", None)
        messages.error(
            request=request,
            # SECURITY: `request_id` is escaped.
            message=mark_safe(  # nosec
                _(
                    "<strong>Something went wrong during authentication.</strong> "
                    "<p>This is not your fault, and unfortunately there's not "
                    "much you can do about it except maybe try again later.</p>"
                    "If you want to let us know about this failure, please add "
                    "this code <strong>{request_id}</strong> to your "
                    "message."
                ).format(request_id=escape(request_id))
            ),
        )
        return redirect("start")
