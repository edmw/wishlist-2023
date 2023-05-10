from typing import Any

from django.db import models

from ..types import Preference


class PreferenceField(models.IntegerField):
    """Model field describing a wish’s preference."""

    description = "Preference of the wish"

    def __init__(self, *args: Any, **kwargs: Any):
        """Initializes the field as integer field.

        Configures the field according to the properties of the preference type.
        """
        kwargs["verbose_name"] = "Preference"
        kwargs["help_text"] = self.description
        kwargs["db_column"] = "preference"
        kwargs["choices"] = Preference.choices
        kwargs["null"] = False
        kwargs["blank"] = False
        kwargs["default"] = Preference.default
        super().__init__(*args, **kwargs)
