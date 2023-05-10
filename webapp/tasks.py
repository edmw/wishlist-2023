"""The webapp’s tasks."""

from celery.utils.log import get_task_logger
from django.core import management

from webapp.scheduler import scheduler

logger = get_task_logger(__name__)


@scheduler.task(name="webapp.sessions_cleanup")
def sessions_cleanup() -> None:
    """Task to cleanup expired sessions by using Django management command.

    NOTE: Tasks will run with the celery worker! Not with the Django webapp.
    """
    from webapp.services import TaskLoggingService

    TaskLoggingService.task_begin("Clearing sessions", logger=logger)

    management.call_command("clearsessions", verbosity=0)

    TaskLoggingService.task_end("Done clearing sessions", logger=logger)
