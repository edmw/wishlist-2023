# Gunicorn webserver configuration.
# This is used for production (not locally, besides testing).
# Use in a secure environment only (see section: Security).

import logging
from datetime import datetime, timezone
from typing import Any, cast

import pythonjsonlogger
from gunicorn import glogging

PROJECT_NAME = "Wishlist"

GUNICORN_LOG_LEVEL = "WARNING"
GUNICORN_ACCESS_LOG = "gunicorn.access"
GUNICORN_ERROR_LOG = "gunicorn.error"

LOG_META_PROJECT_NAME = "meta.project.name"
LOG_META_PROJECT_COMPONENT = "meta.project.component"


# Server configuration:

bind = "0.0.0.0:8000"
worker_class = "gthread"
workers = 4
threads = 4

# Security configuration:

# The setting forwarded_allow_ips defines front-end’s ips from which it is
# allowed to forward secure headers. This restriction is disabled. As a result
# this gunicorn configuration must be used ONLY in secure environments ...
forwarded_allow_ips = "*"

# Logging configuration:

accesslog = "-"  # None to disable; '-' for stdout


class Logger(glogging.Logger):
    """Logger class to be used by Gunicorn logging.
    Extends Gunicorn’s original logger class.
    """

    def now(self) -> str:
        """Override to get current time for logging in ISO 8601 format."""
        return datetime.now(timezone.utc).isoformat()


logger_class = Logger


class JsonFormatter(pythonjsonlogger.json.JsonFormatter):
    """Log formatter for structured logging using JSON."""

    def __init__(self, *args: Any, **kwargs: Any):
        self.fields = kwargs.pop("fields", None)
        super().__init__(*args, **kwargs)

    def parse(self) -> list[str]:
        """Returns a list of fields to include in all log messages."""
        return self.fields or super().parse()

    def add_fields(
        self,
        log_data: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        super().add_fields(log_data, record, message_dict)

        if record.name == GUNICORN_ACCESS_LOG:
            # Populate fields on log record after renaming.
            for field in self.fields or self._required_fields:
                default_name = field
                name = self.rename_fields.get(field, default_name)
                if name not in log_data or log_data[name] is None:
                    if hasattr(record, "args") and record.args:
                        if isinstance(record.args, dict):
                            log_data[name] = record.args.get(field)


# Configure log formatter for structured logging using JSON
# for gunicorn’s access log.

logconfig_dict = cast(dict[str, dict], glogging.CONFIG_DEFAULTS)

logconfig_dict["formatters"]["access_log_json"] = {
    "()": JsonFormatter,
    "fields": [
        LOG_META_PROJECT_NAME,
        LOG_META_PROJECT_COMPONENT,
        "name",
        "levelname",
        "{x-request-id}i",
        "t",
        "r",
        "m",
        "U",
        "L",
        "f",
        "s",
        "b",
        "H",
        "h",
        "{x-forwarded-for}i",
        "u",
        "a",
    ],
    "static_fields": {
        LOG_META_PROJECT_NAME: PROJECT_NAME,
        LOG_META_PROJECT_COMPONENT: "Gunicorn",
    },
    "rename_fields": {
        "t": "@timestamp",
        "name": "log.name",
        "levelname": "log.level",
        "{x-request-id}i": "http.request.id",
        "r": "http.request.full",
        "m": "http.request.method",
        "U": "http.request.path",
        "L": "http.request.time",
        "f": "http.request.referer",
        "s": "http.response.status_code",
        "b": "http.response.bytes",
        "H": "network.protocol",
        "h": "source.ip",
        "{x-forwarded-for}i": "client.ip",
        "u": "user.name",
        "a": "user_agent",
    },
}
logconfig_dict["handlers"]["access_log_handler"] = {
    "class": "logging.StreamHandler",
    "formatter": "access_log_json",
    "stream": "ext://sys.stdout",
}
logconfig_dict["loggers"][GUNICORN_ACCESS_LOG]["handlers"] = ["access_log_handler"]
logconfig_dict["loggers"][GUNICORN_ACCESS_LOG]["level"] = GUNICORN_LOG_LEVEL
logconfig_dict["loggers"][GUNICORN_ACCESS_LOG]["propagate"] = False

logconfig_dict["formatters"]["error_log_json"] = {
    "()": JsonFormatter,
    "fields": [
        LOG_META_PROJECT_NAME,
        LOG_META_PROJECT_COMPONENT,
        "name",
        "levelname",
        "asctime",
        "message",
        "process",
    ],
    "static_fields": {
        LOG_META_PROJECT_NAME: PROJECT_NAME,
        LOG_META_PROJECT_COMPONENT: "Gunicorn",
    },
    "rename_fields": {
        "name": "log.name",
        "levelname": "log.level",
        "asctime": "@timestamp",
        "message": "message",
        "process": "process.pid",
    },
    "datefmt": "%Y-%m-%dT%H:%M:%S%z",
}
logconfig_dict["handlers"]["error_log_handler"] = {
    "class": "logging.StreamHandler",
    "formatter": "error_log_json",
    "stream": "ext://sys.stdout",
}
logconfig_dict["loggers"][GUNICORN_ERROR_LOG]["handlers"] = ["error_log_handler"]
logconfig_dict["loggers"][GUNICORN_ERROR_LOG]["level"] = GUNICORN_LOG_LEVEL
logconfig_dict["loggers"][GUNICORN_ERROR_LOG]["propagate"] = False


# Configure gunicorn’s internal logging to have the same format as the webapp’s
# logging (execept the prefix).
glogging.Logger.error_fmt = (
    f"[{PROJECT_NAME}/Gunicorn] " + "%(levelname)s %(asctime)s,%(msecs)03d [%(process)d] %(message)s"
)
