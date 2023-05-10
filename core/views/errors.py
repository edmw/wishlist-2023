"""All about viewing errors."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import requires_csrf_token


@requires_csrf_token
def internal_server_error(request: HttpRequest) -> HttpResponse:
    """The view for an internal server error."""
    return render(request, "500.html", status=500)


@requires_csrf_token
def bad_request(request: HttpRequest, exception: Exception) -> HttpResponse:
    """The view for a bad request error."""
    return render(request, "400.html", status=400)


@requires_csrf_token
def not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    """The view for a not found error."""
    return render(request, "404.html", status=404)


@requires_csrf_token
def forbidden(request: HttpRequest, exception: Exception) -> HttpResponse:
    """The view for a forbidden error."""
    return render(request, "403.html", status=403)
