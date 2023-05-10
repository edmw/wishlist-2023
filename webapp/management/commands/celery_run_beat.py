"""Celery Run beat command."""

from typing import Any

from celery.apps.beat import Beat

from webapp.scheduler import scheduler

from ._base import SupportsDebugging, SupportsLogging, WebappBaseCommand


class Command(SupportsLogging, SupportsDebugging, WebappBaseCommand):
    """Celery Run beat command: Starts the Celery beat."""

    help = "Runs the webapp’s Celery beat."

    def handle(self, *args: Any, **options: Any) -> None:
        """Starts Celery beat."""
        super().handle(*args, **options)

        self.banner(["WEBAPP BEAT RUN", self.help])

        Beat(app=scheduler, loglevel=self.log_level_name).run()
