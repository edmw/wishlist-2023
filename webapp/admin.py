"""The webapp’s admin site."""

import logging

from django.conf import settings as django_settings
from django.contrib.admin import AdminSite
from django.contrib.admin.apps import AdminConfig
from django.http import HttpRequest

from core.apps import CoreConfig

logger = logging.getLogger(__name__)


class WebappAdminConfig(AdminConfig):
    """Webapp admin configuration."""

    default_site = "webapp.admin.WebappAdminSite"


class WebappAdminSite(AdminSite):
    """Webapp admin site. Replacement for default admin side (see settings)."""

    site_header = (
        "Webapp Administration"
        f" ({CoreConfig.verbose_name}/{django_settings.ENVIRONMENT}/{django_settings.VERSION})"
    )

    def get_app_list(self, request: HttpRequest, app_label: str | None = None) -> list[dict]:
        """Gets the list of apps and models with custom ordering."""
        admin_apps = django_settings.ADMIN_SITE_APPS
        # get app list
        app_list = super().get_app_list(request, app_label)
        # reorder app list by index
        app_list.sort(key=lambda x: admin_apps.get(x["app_label"].lower(), 1))
        return app_list
