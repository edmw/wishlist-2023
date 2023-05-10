"""Celery Run worker command."""

from functools import partial
from typing import Any

from celery.bin.celery import celery
from django.utils import autoreload

from ._base import (
    SupportsAutoreloading,
    SupportsDebugging,
    SupportsLogging,
    WebappBaseCommand,
)


class Command(SupportsLogging, SupportsDebugging, SupportsAutoreloading, WebappBaseCommand):
    """Celery Run worker command: Starts the Celery worker."""

    help = "Runs the webapp’s celery worker."

    def restart_celery(self, solo: bool = False) -> None:
        """Starts Celery worker:

        A worker consists of a supervisor process and one or more child
        processes or threads from which the tasks are processed in general.

        By specifying `pool=solo` this can be changed in a way that there will
        be no children and any task will be processed by the supervisor itself.
        The reason for doing this is that we want to be able to attach a
        debugger to the worker process (see webapp_run command).

        Arguments:
            solo: If true, use solo mode. Defaults to False.
        """
        arguments = ["--app", "webapp", "worker", "--loglevel", self.log_level_name]
        if solo:
            arguments += ["--pool", "solo"]

        celery.main(
            args=arguments,
            standalone_mode=False,
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Starts the Celery worker.

        Starts a single worker with a single worker process.
        """
        super().handle(*args, **options)

        if self.is_initial_run:
            self.banner(["WEBAPP WORKER RUN", self.help])

        if self.is_main_run and self.enable_debugging:
            self.banner(["Starting", "debugger"])
            self.debugpy_listen()

        self.banner(["Running" if self.is_main_run else "Starting"], discreet=True)
        autoreload.run_with_reloader(partial(self.restart_celery, self.enable_debugging))
