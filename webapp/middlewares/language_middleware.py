import inspect
import logging
import re
from collections import namedtuple
from contextlib import contextmanager
from typing import Callable, Generator

from django.conf import settings as django_settings
from django.http import HttpRequest, HttpResponse
from django.utils.decorators import sync_and_async_middleware

from webapp.services import LanguageService

logger = logging.getLogger(__name__)


RE_HTTP_ACCEPT_LANGUAGE = re.compile(
    "((?:(?:[a-zA-Z]+(?:-[a-zA-Z0-9]+){0,2})|\\*)(?:;q=[0-1](?:\\.[\\d]+)?)?)\\s*(?:,|$)\\s*"
)


Language = namedtuple("Language", "code region script quality")


def parse_languages(accept_language_string: str) -> list[Language]:
    accept_languages = RE_HTTP_ACCEPT_LANGUAGE.findall(accept_language_string)
    languages = []
    for accept_language in accept_languages:
        identifier = accept_language.split(";")
        identifier_count = len(identifier)
        if identifier_count > 2:
            continue
        tag = identifier[0].split("-")
        match len(tag):
            case 1:
                language = tag[0].lower()
                region = None
                script = None
            case 2:
                language = tag[0].lower()
                region = tag[1]
                script = None
            case 3:
                language = tag[0].lower()
                region = tag[2]
                script = tag[1]
            case _:
                continue
        if identifier_count == 2:
            components = identifier[1].split("=")
            components_count = len(components)
            quality = float(components[1]) if components_count == 2 else 1.0
        else:
            quality = 1.0
        languages.append(Language(language, region, script, quality))
    return sorted(languages, key=lambda language: language.quality, reverse=True)


def pick_language_code(language_codes: list[str], accepted_languages: list[Language]) -> str | None:
    # This is a sanity check while developing which can be safely removed in production.
    assert len(language_codes) > 0  # nosec

    for language in accepted_languages:
        if language.code in language_codes:
            return language.code
    return None


def language_code_from_request_query(request: HttpRequest, language_codes: list[str]) -> str | None:
    if query_language := request.GET.get("lang"):
        if query_language in language_codes:
            return query_language
    return None


def language_code_from_request_user(request: HttpRequest, language_codes: list[str]) -> str | None:
    if user := getattr(request, "user", None):
        if user_language := getattr(user, "language", None):
            if user_language in language_codes:
                return user_language
    return None


def language_code_from_http_header(request: HttpRequest, language_codes: list[str]) -> str | None:
    if accept_language_string := request.META.get("HTTP_ACCEPT_LANGUAGE"):
        if languages := parse_languages(accept_language_string):
            return pick_language_code(language_codes, languages)
    return None


@contextmanager
def language_for_request(request: HttpRequest, language_codes: list[str]) -> Generator[None]:
    language_code = None

    if request.path.startswith("/admin"):
        # admin is always english
        language_code = "en"

    if not language_code:
        language_code = language_code_from_request_query(request, language_codes)

    if not language_code:
        language_code = language_code_from_request_user(request, language_codes)

    if not language_code:
        language_code = language_code_from_http_header(request, language_codes)

    if language_code:
        LanguageService.activate(language_code=language_code)

    yield

    if language_code:
        LanguageService.deactivate()


@sync_and_async_middleware
def language_middleware(get_response: Callable) -> Callable:
    available_language_codes = [language[0] for language in django_settings.LANGUAGES]

    if inspect.iscoroutinefunction(get_response):

        async def async_middleware(request: HttpRequest) -> HttpResponse:
            with language_for_request(request, available_language_codes):
                response = await get_response(request)
            return response

        return async_middleware

    else:

        def middleware(request: HttpRequest) -> HttpResponse:
            with language_for_request(request, available_language_codes):
                response = get_response(request)
            return response

        return middleware
