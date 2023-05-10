"""The readiness probe."""

import logging
from http import HTTPStatus

from django.http import HttpRequest, HttpResponse
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)

logger = logging.getLogger(__name__)


@api_view(["GET"])
@authentication_classes([])
@permission_classes([])
def readiness(request: HttpRequest) -> HttpResponse:
    """Readiness probe for Kubernetes.

    The kubelet uses readiness probes to know when a container is ready to start
    accepting traffic. A Pod is considered ready when all of its containers are
    ready. One use of this signal is to control which Pods are used as backends
    for Services. When a Pod is not ready, it is removed from Service load
    balancers.
    """
    return HttpResponse(status=HTTPStatus.OK, content_type="text/plain")
