import logging
import types
from typing import Any

import billiard.einfo
import celery
import celery.app.task
import celery.apps.worker
import celery.bootsteps
import celery.signals
import structlog

logger = logging.getLogger(__name__)


class WorkerInit(celery.bootsteps.Step):
    def _on_task_prerun(
        self,
        sender: celery.app.task.Task,
        task_id: str,
        task: celery.app.task.Task,
        args: Any,
        kwargs: Any,
        **_: Any,
    ) -> None:
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            **{
                "task.id": task_id,
                "task.name": task.name,
            },
        )

    def _on_task_success(
        self,
        sender: celery.app.task.Task,
        result: Any,
        **_: Any,
    ) -> None:
        logger.info("task_success", extra={"result": result})

    def _on_task_failure(
        self,
        sender: celery.app.task.Task,
        task_id: str,
        exception: Exception,
        args: Any,
        kwargs: Any,
        traceback: types.TracebackType,
        einfo: billiard.einfo.ExceptionInfo,
        **_: Any,
    ) -> None:
        throws = getattr(sender, "throws", ())
        if isinstance(exception, throws):
            logger.info(
                "task_failure",
                extra={"error": str(exception)},
            )
        else:
            logger.exception(
                "task_failure",
                extra={"error": str(exception), "exception": exception},
            )

    def __init__(self, parent: celery.apps.worker.Worker, **kwargs: Any):
        super().__init__(parent, **kwargs)

        celery.signals.task_prerun.connect(self._on_task_prerun)


def init_celery(**kwargs: Any) -> celery.Celery:
    """Initialise Celery app with configuration from webapp settings."""
    app = celery.Celery("webapp")
    app.config_from_object("django.conf:settings", namespace="CELERY")

    if kwargs:
        # update configuration with given kwargs
        app.conf.update(**kwargs)

    assert app.steps is not None  # nosec
    app.steps["worker"].add(WorkerInit)

    app.autodiscover_tasks()

    return app


scheduler = init_celery()
