"""The webapp’s applications configurations."""

from django.apps import AppConfig
from django.contrib.staticfiles import apps as staticfiles_apps
from django_celery_beat import apps as celery_beat_apps
from django_celery_results import apps as celery_results_apps


class WebappConfig(AppConfig):
    """Webapp application configuration."""

    name = "webapp"
    verbose_name = "Webapp"

    def ready(self) -> None:
        import webapp.signals


class StaticFilesConfig(staticfiles_apps.StaticFilesConfig):
    ignore_patterns = [".*", "*~", "root"]


class CeleryBeatConfig(celery_beat_apps.BeatConfig):
    """Celery beat application configuration."""

    verbose_name = "Celery Periodic Tasks"


class CeleryResultsConfig(celery_results_apps.CeleryResultConfig):
    """Celery result application configuration."""

    verbose_name = "Celery Tasks Results"
