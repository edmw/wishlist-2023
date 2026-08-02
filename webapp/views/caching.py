"""Caching services for views."""

from typing import Any, Protocol, Type

from django.http import HttpRequest
from django.http.response import HttpResponseBase
from django.utils.cache import add_never_cache_headers
from django.views.decorators.cache import cache_page


class ViewCallable(Protocol):
    """Typing stub for a callable view function."""

    def __call__(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseBase:
        """Handles request, returns response."""
        ...


class _SupportsAsView(Protocol):
    cache_timeout: int

    @classmethod
    def as_view(cls, **initkwargs: Any) -> ViewCallable: ...


class CacheMixin:
    """Adds caching to the view.

    Uses the requests fully-qualified URL as cache key. This means every request
    to that URL will use the same cached version, regardless of a session or
    cookies.
    """

    cache_timeout = 60

    @classmethod
    def as_view(cls: Type[_SupportsAsView], **initkwargs: Any) -> ViewCallable:
        """Wraps the the view with the cache handler."""
        return cache_page(cls.cache_timeout)(super().as_view(**initkwargs))


class _SupportsDispatch(Protocol):
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseBase: ...


class AddNeverCacheMixin:
    """Adds never caching cache control headers to GET requests."""

    def dispatch(
        self: _SupportsDispatch, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        """Adds never caching cache control headers to GET requests."""
        response = super().dispatch(request, *args, **kwargs)
        if request.method and request.method.upper() == "GET":
            add_never_cache_headers(response)
        return response
