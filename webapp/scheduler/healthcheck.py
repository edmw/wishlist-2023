import logging
from datetime import timedelta

from celery import states
from django.utils import timezone

from .scheduler import scheduler

logger = logging.getLogger(__name__)

HEALTHCHECK_COMPONENT = "webapp.scheduler"
HEALTHCHECK_TASK_RESULTS_TIMEDELTA = timedelta(days=1)


def _healthcheck_task_result(check_id: int) -> tuple[bool, str, int, str]:
    from webapp.services import SchedulingService

    start_time = timezone.now() - HEALTHCHECK_TASK_RESULTS_TIMEDELTA
    counts = SchedulingService.count_task_results(since=start_time)
    success_count = counts.get(states.SUCCESS, 0)
    failure_count = counts.get(states.FAILURE, 0)
    return (
        failure_count == 0,
        HEALTHCHECK_COMPONENT,
        check_id,
        f"has completed {success_count} tasks successfully "
        f"and {failure_count} tasks with a failure "
        f"since {str(HEALTHCHECK_TASK_RESULTS_TIMEDELTA).removesuffix(', 0:00:00')}",
    )


def healthcheck() -> list[tuple[bool, str, int, str]]:
    """Performs various checks to determine the health status of celery app."""
    from django.conf import settings as django_settings

    from webapp.services import CacheManager

    broker_connection = scheduler.connection_for_read()
    broker_uri = broker_connection.as_uri()

    healthcheck_task_result = None
    # check#4 returns the status of recently completed tasks
    # because this check needs to access the database, the result will be cached for 15 minutes
    with CacheManager(key="webapp.scheduler.healthcheck.tasks_result", timeout=900) as cm:
        healthcheck_task_result = cm.get()
        if not healthcheck_task_result:
            healthcheck_task_result = _healthcheck_task_result(4)
            cm.set(value=healthcheck_task_result)

    # check#1 just returns the configured broker url and is always true
    # check#2 returns the state of the lazy connection which may be false
    #   without real activity
    # check#3 returns the name of the configured default queue
    # more checks could return the current state of the workers (but be aware,
    # this requires some network communication):
    # stats = app.control.inspect().stats()
    healthcheck_results = [
        (broker_connection is not None, HEALTHCHECK_COMPONENT, 1, f"has connection for {broker_uri}"),
        (
            broker_connection is not None and broker_connection.connected,
            HEALTHCHECK_COMPONENT,
            2,
            f"is connected to {broker_uri}",
        ),
        (
            True,
            HEALTHCHECK_COMPONENT,
            3,
            f"is using task queue {django_settings.CELERY_TASK_DEFAULT_QUEUE}",
        ),
    ]

    if healthcheck_task_result:
        healthcheck_results.append(healthcheck_task_result)

    return healthcheck_results
