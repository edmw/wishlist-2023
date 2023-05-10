"""Provides service functions for language handling."""

from contextlib import contextmanager
from typing import Generator

from django.utils import translation


class LanguageService:
    """Service class providing a collection of static functions for language handling."""

    @staticmethod
    def activate(*, language_code: str) -> None:
        translation.activate(language_code)
        try:
            import humanize

            if language_code != "en":
                # activates translation
                humanize.activate(language_code)
            else:
                # activates default which is english
                humanize.deactivate()
        except ImportError:
            pass

    @staticmethod
    def deactivate() -> None:
        translation.deactivate()
        try:
            import humanize

            humanize.deactivate()
        except ImportError:
            pass

    @contextmanager
    @staticmethod
    def activated(*, language_code: str) -> Generator[None, None, None]:
        LanguageService.activate(language_code=language_code)
        yield
        LanguageService.deactivate()

    @staticmethod
    def get_language_code() -> str:
        return translation.get_language() or "en"

    @staticmethod
    def get_language_bidi() -> bool:
        return translation.get_language_bidi()
