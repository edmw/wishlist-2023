"""The configuration of the Core Health application."""

from django.apps import AppConfig


class CoreHealthAppConfig(AppConfig):
    """Core Health application configuration."""

    name = "core_health"
    verbose_name = "Webapp Health"
    description = "HEALTHCHECKS FOR WEBAPP."

    def ready(self) -> None:
        """Initializes the Core Health application: Called once when the
        application has become ready.
        """
        pass  # nothing to do, just be ready
