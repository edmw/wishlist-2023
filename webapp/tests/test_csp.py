"""Tests for Content Security Policy handling."""

import re
from http import HTTPStatus

import pytest
from django.test import Client

pytestmark = pytest.mark.django_db


def _extract_html_nonces(html: str) -> list[str]:
    return re.findall(r'nonce="([^"]+)"', html)


def _parse_csp_directives(csp_header: str) -> dict[str, set[str]]:
    directives: dict[str, set[str]] = {}
    for directive in csp_header.split(";"):
        directive = directive.strip()
        if not directive:
            continue
        name, *values = directive.split()
        directives[name] = set(values)
    return directives


def test_start_page_sets_csp_header_and_nonce(client: Client) -> None:
    """The start page should emit a CSP header and reuse the same nonce in HTML."""
    response = client.get("/")

    assert response.status_code == HTTPStatus.OK

    csp_header = response.headers["Content-Security-Policy"]
    html = response.content.decode("utf-8")
    nonces = _extract_html_nonces(html)

    assert nonces
    assert len(set(nonces)) == 1
    assert f"nonce-{nonces[0]}" in csp_header
    assert "script-src" in csp_header
    assert "style-src" in csp_header


def test_start_page_csp_header_contains_expected_directives(client: Client) -> None:
    """The CSP policy should include the security-critical directives from settings."""
    response = client.get("/")

    assert response.status_code == HTTPStatus.OK

    csp_header = response.headers["Content-Security-Policy"]
    directives = _parse_csp_directives(csp_header)

    assert "default-src" in directives
    assert "script-src" in directives
    assert "style-src" in directives
    assert "img-src" in directives

    assert "'self'" in directives["default-src"]
    assert "'self'" in directives["script-src"]
    assert "'self'" in directives["style-src"]
    assert "'self'" in directives["img-src"]
    assert "data:" in directives["img-src"]


def test_start_page_generates_fresh_nonce_per_request(client: Client) -> None:
    """Nonce values should be request-scoped and not reused between responses."""
    response_1 = client.get("/")
    response_2 = client.get("/")

    assert response_1.status_code == HTTPStatus.OK
    assert response_2.status_code == HTTPStatus.OK

    html_1 = response_1.content.decode("utf-8")
    html_2 = response_2.content.decode("utf-8")
    nonces_1 = _extract_html_nonces(html_1)
    nonces_2 = _extract_html_nonces(html_2)

    assert nonces_1
    assert nonces_2
    assert len(set(nonces_1)) == 1
    assert len(set(nonces_2)) == 1
    assert nonces_1[0] != nonces_2[0]
