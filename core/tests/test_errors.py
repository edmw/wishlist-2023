from http import HTTPStatus

import pytest
from django.core.exceptions import BadRequest, PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.test.client import Client
from django.urls import path
from pytest_django.asserts import assertContains, assertTemplateUsed

from webapp.urls import urlpatterns


def bad_request_view(request: HttpRequest) -> HttpResponse:
    raise BadRequest()


def forbidden_view(request: HttpRequest) -> HttpResponse:
    raise PermissionDenied()


urlpatterns = urlpatterns + [
    path("400/", bad_request_view),
    path("403/", forbidden_view),
]

handler400 = "core.views.errors.bad_request"
handler403 = "core.views.errors.forbidden"
handler404 = "core.views.errors.not_found"
handler500 = "core.views.errors.internal_server_error"


@pytest.mark.urls(__name__)
def test_bad_request(client: Client) -> None:
    response = client.get("/400/")
    assertContains(response, "400 BAD REQUEST", status_code=HTTPStatus.BAD_REQUEST)
    assertTemplateUsed(response=response, template_name="400.html")


@pytest.mark.urls(__name__)
def test_forbidden(client: Client) -> None:
    response = client.get("/403/")
    assertContains(response, "403 FORBIDDEN", status_code=HTTPStatus.FORBIDDEN)
    assertTemplateUsed(response=response, template_name="403.html")


@pytest.mark.urls(__name__)
def test_not_found(client: Client) -> None:
    response = client.get("/404/")
    assertContains(response, "404 NOT FOUND", status_code=HTTPStatus.NOT_FOUND)
    assertTemplateUsed(response=response, template_name="404.html")
