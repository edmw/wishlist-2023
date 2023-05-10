from typing import Any

from django.db import models

from ..types import Language


class LanguageField(models.CharField):
    """Model field describing a user’s language."""

    description = "Language of the user"

    def __init__(self, *args: Any, **kwargs: Any):
        """Initializes the field as char field.

        Configures the field according to the properties of the language type.
        """
        if "verbose_name" not in kwargs:
            kwargs["verbose_name"] = "Language"
        if "help_text" not in kwargs:
            kwargs["help_text"] = self.description
        if "db_column" not in kwargs:
            kwargs["db_column"] = "language"
        kwargs["blank"] = True
        kwargs["max_length"] = Language.max_length
        kwargs["choices"] = Language.choices
        kwargs["default"] = Language.default
        super().__init__(*args, **kwargs)
