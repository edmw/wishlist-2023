"""The liveness probe."""

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
def liveness(request: Request) -> Response:
    """Liveness probe for Kubernetes.

    The kubelet uses liveness probes to know when to restart a container. For
    example, liveness probes could catch a deadlock, where an application is
    running, but unable to make progress. Restarting a container in such a state
    can help to make the application more available despite bugs.
    """
    return Response(status=HTTPStatus.OK, content_type="text/plain")
