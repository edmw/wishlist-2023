"""Make Translations command."""

import glob
import os
from typing import Any

from django.core import management

from ._base import WebappBaseCommand


class Command(WebappBaseCommand):
    """Make Translations command: Creates language translations for all apps."""

    help = "Creates translation(s) for apps."

    def pin_pot_creation_date(self, locale_paths: list[str], locale_languages: list[str]) -> None:
        """Pins POT creation date to a specific date. This prevents unnecessary
        conflicts when merging different versions.
        """
        import polib

        for locale_path in locale_paths:
            for language in locale_languages:
                for po_file in glob.glob(os.path.join(locale_path, language, "LC_MESSAGES", "*.po")):
                    po = polib.pofile(po_file)
                    po.metadata["POT-Creation-Date"] = "2001-01-01 00:00+0000"
                    po.save(po_file)

    def handle(self, *args: Any, **options: Any) -> None:
        """Creates language translations.

        Determines the desired languages and first creates the language files
        and then compiles them.
        """
        self.banner(["WEBAPP MAKE TRANSLATIONS", self.help])

        if os.environ.get("DJANGO_SETTINGS_MODULE"):
            from django.conf import settings

            locale_paths = settings.LOCALE_PATHS
            locale_languages = [language[0] for language in settings.LANGUAGES]
        else:
            locale_paths = [os.path.join("conf", "locale"), "locale"]
            locale_languages = ["en"]

        command = ("makemessages", "--no-color", "--add-location=never") + tuple(
            f"--locale={language}" for language in locale_languages
        )
        management.call_command(*command)

        command = (
            "compilemessages",
            "--no-color",
            "--ignore=.git",
            "--ignore=.git/**",
            "--ignore=.venv/**",
        )
        management.call_command(*command)

        self.pin_pot_creation_date(locale_paths, locale_languages)
