import logging
from http import HTTPStatus
from typing import Any

from django.core.exceptions import SuspiciousOperation
from django.http import HttpResponse, JsonResponse
from django.utils.log import log_response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


def exception_handler(exc: Exception, context: dict[str, Any]) -> HttpResponse:
    """Exception handler for REST API calls: First, uses DRF standard exception
    handling, then wraps a SuspiciousOperation into a 400 Bad Request JSON
    response and finally, wraps any unhandled exception into a 500 Internal
    Server Error JSON response.
    """
    if response := drf_exception_handler(exc, context):
        return response

    # response for any unhandled exception

    if isinstance(exc, SuspiciousOperation):
        status = HTTPStatus.BAD_REQUEST
        data = {"detail": "Bad Request (400)"}
    else:
        status = HTTPStatus.INTERNAL_SERVER_ERROR
        data = {"detail": "Server Error (500)"}

    response = JsonResponse(data, status=status)

    # log response (including traceback)
    request = context["request"]
    log_response(
        "%s: %s",
        str(exc),
        request.path,
        response=response,
        request=request,
        logger=logger,
        exception=exc,
    )

    return response
