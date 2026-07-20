"""The readiness probe."""

import logging
from http import HTTPStatus

from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.request import Request
from rest_framework.response import Response

logger = logging.getLogger(__name__)


@api_view(["GET"])
@authentication_classes([])
@permission_classes([])
def readiness(request: Request) -> Response:
    """Readiness probe for Kubernetes.

    The kubelet uses readiness probes to know when a container is ready to start
    accepting traffic. A Pod is considered ready when all of its containers are
    ready. One use of this signal is to control which Pods are used as backends
    for Services. When a Pod is not ready, it is removed from Service load
    balancers.
    """
    return Response(status=HTTPStatus.OK, content_type="text/plain")
