import inspect
import logging
from contextlib import contextmanager
from typing import Callable, Generator

from django.http import HttpRequest, HttpResponse
from django.utils.decorators import sync_and_async_middleware

from webapp.constants import REQUEST_ATTR_REQUEST_ID
from webapp.services import RequestService

logger = logging.getLogger(__name__)


@contextmanager
def for_request(request: HttpRequest) -> Generator[None]:
    setattr(request, REQUEST_ATTR_REQUEST_ID, RequestService.get_request_id(request=request))

    yield


@sync_and_async_middleware
def request_middleware(get_response: Callable) -> Callable:
    if inspect.iscoroutinefunction(get_response):

        async def async_middleware(request: HttpRequest) -> HttpResponse:
            with for_request(request):
                response = await get_response(request)
            return response

        return async_middleware

    else:

        def middleware(request: HttpRequest) -> HttpResponse:
            with for_request(request):
                response = get_response(request)
            return response

        return middleware
