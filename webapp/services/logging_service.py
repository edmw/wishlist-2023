"""Provides service functions for logging."""

import logging
from copy import copy
from logging import Logger
from typing import Any

from django.http import HttpRequest

from webapp import constants


def _log(
    level: int,
    message: str,
    *args: Any,
    logger: Logger,
    log_class: str,
    extra: dict | None = None,
) -> None:
    if not extra:
        extra = {}
    extra[constants.LOG_CLASS_KEY] = log_class
    logger.log(
        level,
        f"{log_class}: " + message,
        *args,
        extra=extra,
    )


class LoggingService:
    """Service class providing a collection of static functions for logging."""

    SUSPICIOUS_OPERATION = "SuspiciousOperation"

    @staticmethod
    def suspicious_request(
        message: str,
        *args: Any,
        logger: Logger,
        request: HttpRequest,
        extra: dict | None = None,
    ) -> None:
        log_class = LoggingService.SUSPICIOUS_OPERATION
        if not extra:
            extra = {}
        if user := request.user:
            if user.is_authenticated:
                extra[constants.LOG_WEBAPP_REQUESTING_USER_KEY] = copy(user)
        extra[constants.LOG_CLASS_KEY] = log_class
        logger.warning(
            f"{log_class}: " + message,
            *args,
            extra=extra,
        )


class SignalLoggingService(LoggingService):
    """Maps semantic logging functions for signals to technical logging calls."""

    @staticmethod
    def signal_receive(
        message: str,
        *args: Any,
        logger: Logger,
        extra: dict | None = None,
    ) -> None:
        _log(
            logging.INFO,
            message,
            *args,
            logger=logger,
            log_class="SignalReceive",
            extra=extra,
        )


class TaskLoggingService(LoggingService):
    """Maps semantic logging functions for tasks to technical logging calls."""

    @classmethod
    def _merge_extra(cls, task_data: dict | None, extra: dict | None) -> dict | None:
        if task_data:
            return {**(extra or {}), **{f"task.data.{key}": value for key, value in task_data.items()}}
        return extra

    @staticmethod
    def task_begin(
        message: str,
        *args: Any,
        logger: Logger,
        data: dict | None = None,
        extra: dict | None = None,
    ) -> None:
        _log(
            logging.INFO,
            message,
            *args,
            logger=logger,
            log_class="TaskBegin",
            extra=TaskLoggingService._merge_extra(data, extra),
        )

    @staticmethod
    def task_end(
        message: str,
        *args: Any,
        logger: Logger,
        data: dict | None = None,
        extra: dict | None = None,
    ) -> None:
        _log(
            logging.INFO,
            message,
            *args,
            logger=logger,
            log_class="TaskEnd",
            extra=TaskLoggingService._merge_extra(data, extra),
        )

    @staticmethod
    def task_retry(
        message: str,
        *args: Any,
        logger: Logger,
        data: dict | None = None,
        extra: dict | None = None,
    ) -> None:
        _log(
            logging.INFO,
            message,
            *args,
            logger=logger,
            log_class="TaskRetry",
            extra=TaskLoggingService._merge_extra(data, extra),
        )

    @staticmethod
    def task_fail(
        message: str,
        *args: Any,
        logger: Logger,
        data: dict | None = None,
        extra: dict | None = None,
    ) -> None:
        _log(
            logging.WARNING,
            message,
            *args,
            logger=logger,
            log_class="TaskFail",
            extra=TaskLoggingService._merge_extra(data, extra),
        )


class AuthLoggingService(LoggingService):
    """Maps semantic logging functions for authentication to technical logging calls."""

    @staticmethod
    def login_fail(
        message: str,
        *args: Any,
        logger: Logger,
        request: HttpRequest,
        provider_id: str,
        error: str | None,
        exception: Exception | None,
        context: dict | None,
    ) -> None:
        """Logs"""
        _log(
            logging.ERROR,
            message,
            *args,
            logger=logger,
            log_class="AuthLogin",
            extra={
                "request": request,
                "auth.provider": provider_id,
                "auth.error": str(error),
                "auth.exception": str(exception),
                "auth.context": context,
            },
        )
