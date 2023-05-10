"""The health checks."""

from http import HTTPStatus
from typing import Any

from django.conf import settings as django_settings
from django.http import HttpResponse
from django.utils.encoding import smart_str
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import BaseRenderer, JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response

from core_health.types import HealthCheckResult, HealthCheckResults
from webapp.scheduler import healthcheck as scheduler_healthcheck

from ._permissions import CanCheckHealth


def check_environment() -> list[HealthCheckResult]:
    """Health checks for the environment. Informational, only."""
    return [
        HealthCheckResult(True, "Environment", 0, f"is {django_settings.ENVIRONMENT}"),
    ]


def report() -> list[HealthCheckResult]:
    """Collects all the checks and generates a report in the requested format.

    Check results are tuples of
        (status: bool, component_name: str, check_id: int, check_text: str)
    where component_name and check_id should stay the same over time to allow
    parsing check results in monitoring tools.
    """
    checks = HealthCheckResults()
    checks += check_environment()
    checks += scheduler_healthcheck()

    return checks


class ChecksTextRenderer(BaseRenderer):
    """Renderer for rendering health checks as plain text."""

    media_type = "text/*"
    format = "txt"

    def render(
        self, data: Any, accepted_media_type: str | None = None, renderer_context: dict | None = None
    ) -> str:
        """Converts check results to text-renderable string and renders
        to a string.
        """
        if renderer_context:
            response = renderer_context["response"]
            if response and response.status_code == HTTPStatus.OK:
                # response ok, convert checks to text-renderable string
                checks: list[HealthCheckResult] = data
                data = "\n".join([str(check) for check in checks]) + "\n"

        return smart_str(data, self.charset)


class ChecksJSONRenderer(JSONRenderer):
    """Renderer for rendering health checks as json binary."""

    def render(
        self, data: Any, accepted_media_type: str | None = None, renderer_context: dict | None = None
    ) -> bytes:
        """Converts check results to json-serializeable object and delegates
        rendering to the super-class.
        """
        if renderer_context:
            response = renderer_context["response"]
            if response and response.status_code == HTTPStatus.OK:
                # response ok, convert checks to json-serializable object
                checks: list[HealthCheckResult] = data
                data = [check._asdict() for check in checks]

        return super().render(data, accepted_media_type, renderer_context)


@api_view(["GET"])
@permission_classes([IsAuthenticated, CanCheckHealth])
@renderer_classes([ChecksTextRenderer, ChecksJSONRenderer])
def healthcheck(request: Request) -> HttpResponse:
    """Performs various checks to determine the health status of this
    application.

    NOTE: Healthcheck may be called many times per minute and there is a
    potential danger of a friendly denial-of-service, so be aware and implement
    fast and easy tests, only.
    """
    return Response(report())
