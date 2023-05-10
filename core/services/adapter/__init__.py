"""Core’s adapter services: Services which connect to the outside."""

from ._rest_service_adapter import (
    RESTClientError,
    RESTServiceConnectionError,
    RESTServiceError,
    RESTServiceTimeoutError,
    RESTServiceUnavailableError,
    handle_invalid_response,
)
