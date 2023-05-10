import logging
from functools import partial
from http import HTTPStatus
from urllib.parse import urljoin

import requests
from django.conf import settings as django_settings

from core.models.types import PushoverKey
from core.models.user import User

from ._rest_service_adapter import (
    RESTService,
    RESTServiceError,
    handle_invalid_response,
)

logger = logging.getLogger(__name__)
log_response_time = partial(logger.debug, "Request[time elapsed(s)] = %f")


class PushoverServiceInvalidResponseError(RESTServiceError):
    pass


class PushoverService(RESTService):
    RESTSERVICE_CONNECT_TIMEOUT = django_settings.PUSHOVER_CONNECT_TIMEOUT_MS
    RESTSERVICE_READ_TIMEOUT = django_settings.PUSHOVER_READ_TIMEOUT_MS

    @classmethod
    def _message_url(cls) -> str:
        return urljoin(django_settings.PUSHOVER_SERVICE_URL, "1/messages.json")

    @staticmethod
    def send(
        *,
        user: User,
        subject: str,
        message: str,
        html_message: str | None,
        key: PushoverKey,
    ) -> bool:
        response = PushoverService.post(
            url=PushoverService._message_url(),
            json={
                "token": django_settings.PUSHOVER_APPLICATION_TOKEN,
                "user": key,
                "title": subject,
                "message": html_message or message,
                "html": 1 if html_message else 0,
            },
            expected=(HTTPStatus.OK,),
        )
        log_response_time(response.elapsed.total_seconds())

        @handle_invalid_response(
            service_name="PushoverService",
            service_error=PushoverServiceInvalidResponseError,
        )
        def parse_response(response: requests.Response) -> bool:
            return response.json()["status"] == 1

        return parse_response(response)
