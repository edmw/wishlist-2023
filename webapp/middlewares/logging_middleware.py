import inspect
import logging
from contextlib import contextmanager
from typing import Callable, Generator

import structlog
from django.http import HttpRequest, HttpResponse
from django.utils.decorators import sync_and_async_middleware

from webapp.services import RequestService

logger = logging.getLogger(__name__)


@contextmanager
def logging_for_request(request: HttpRequest) -> Generator[None, None, None]:
    structlog.contextvars.bind_contextvars(request=request)
    structlog.contextvars.bind_contextvars(request_id=RequestService.get_request_id(request=request))

    yield

    structlog.contextvars.clear_contextvars()


@sync_and_async_middleware
def logging_middleware(get_response: Callable) -> Callable:
    if inspect.iscoroutinefunction(get_response):

        async def async_middleware(request: HttpRequest) -> HttpResponse:
            with logging_for_request(request):
                response = await get_response(request)
            return response

        return async_middleware

    else:

        def middleware(request: HttpRequest) -> HttpResponse:
            with logging_for_request(request):
                response = get_response(request)
            return response

        return middleware
