"""Provides service functions for request handling."""

from django.http import HttpRequest


class RequestService:
    """Service class providing a collection of static functions for request handling."""

    @staticmethod
    def get_header(*, request: HttpRequest, header_key: str, meta_key: str) -> str | None:
        """Returns the value for the specified request header.

        This function will lookup the request‘s raw headers first, using the
        specified case-insensitive `header_key`. If this will not succeed
        looks up the header value from the request‘s meta values, using the
        specified case-sensitive `meta_key`.

        Arguments:
            request: The request.
            header_key: Key for the header to be queried, e.g. "User-Agent"
            meta_key: Key for the header to be queried after it has been converted
                to a request meta value, e.g. "HTTP_USER_AGENT"

        Returns:
            The value of the request header if existing, None otherwise.
        """
        if headers := getattr(request, "headers", None):
            return headers.get(header_key)
        return request.META.get(meta_key)

    @staticmethod
    def get_request_id(*, request: HttpRequest) -> str | None:
        """Returns a request‘s id if given in the appropriate request header."""
        return RequestService.get_header(
            request=request, header_key="x-request-id", meta_key="HTTP_X_REQUEST_ID"
        )
