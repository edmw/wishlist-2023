"""Tests for handling of languages in middleware."""

import pytest
from django.conf import settings as django_settings
from django.test.client import RequestFactory
from django.utils.translation import get_language

from webapp.middlewares.language_middleware import language_for_request, parse_languages


def test_parse_accept_language() -> None:
    """Tests use of language code."""
    languages = parse_languages("fr")
    assert len(languages) == 1
    assert languages[0] == ("fr", None, None, 1.0)


def test_parse_accept_language_with_region() -> None:
    """Tests use of region value."""
    languages = parse_languages("en-GB")
    assert len(languages) == 1
    assert languages[0] == ("en", "GB", None, 1.0)


def test_parse_accept_language_with_script() -> None:
    """Tests use of script value."""
    languages = parse_languages("zh-Hant-cn")
    assert len(languages) == 1
    assert languages[0] == ("zh", "cn", "Hant", 1.0)


def test_parse_accept_language_with_quality() -> None:
    """Tests use of quality value."""
    languages = parse_languages("de-CH;q=0.8")
    assert len(languages) == 1
    assert languages[0] == ("de", "CH", None, 0.8)


def test_parse_accept_language_wildcard() -> None:
    """Tests use of wildcard."""
    languages = parse_languages("*;q=0.8")
    assert len(languages) == 1
    assert languages[0] == ("*", None, None, 0.8)


def test_parse_accept_language_full() -> None:
    """Tests use of all features."""
    languages = parse_languages("fr-CH,fr;q=0.9,en;q=0.8,de;q=0.7,*;q=0.5")
    assert len(languages) == 5
    assert languages[0] == ("fr", "CH", None, 1.0)
    assert languages[1] == ("fr", None, None, 0.9)
    assert languages[2] == ("en", None, None, 0.8)
    assert languages[3] == ("de", None, None, 0.7)
    assert languages[4] == ("*", None, None, 0.5)


def test_parse_accept_language_with_whitespace() -> None:
    """Tests use of all features with arbitrary whitespace."""
    languages = parse_languages("fr-CH, fr;q=0.9,  en;q=0.8 , de;q=0.7, *;q=0.5")
    assert len(languages) == 5
    assert languages[0] == ("fr", "CH", None, 1.0)
    assert languages[1] == ("fr", None, None, 0.9)
    assert languages[2] == ("en", None, None, 0.8)
    assert languages[3] == ("de", None, None, 0.7)
    assert languages[4] == ("*", None, None, 0.5)


def test_parse_accept_language_sorted() -> None:
    """Tests sorting by quality values."""
    languages = parse_languages("fr-CA,fr;q=0.2,en-US;q=0.6,en;q=0.4,*;q=0.5")
    assert len(languages) == 5
    assert languages[0] == ("fr", "CA", None, 1.0)
    assert languages[1] == ("en", "US", None, 0.6)
    assert languages[2] == ("*", None, None, 0.5)
    assert languages[3] == ("en", None, None, 0.4)
    assert languages[4] == ("fr", None, None, 0.2)


@pytest.fixture
def available_language_codes() -> list[str]:
    """Returns a list of codes for all available languages from settings."""
    return [language[0] for language in django_settings.LANGUAGES]


def test_with_request_for_en(available_language_codes: list[str]) -> None:
    """Tests for a simple language request header."""
    current = get_language()
    request = RequestFactory().get("/")
    request.META["HTTP_ACCEPT_LANGUAGE"] = "en"
    with language_for_request(request, available_language_codes):
        assert get_language() == "en"
    assert get_language() == current


def test_with_request_for_de(available_language_codes: list[str]) -> None:
    """Tests for a language request header with quality values."""
    current = get_language()
    request = RequestFactory().get("/")
    request.META["HTTP_ACCEPT_LANGUAGE"] = "en;q=0.2,de;q=0.9"
    with language_for_request(request, available_language_codes):
        assert get_language() == "de"
    assert get_language() == current
