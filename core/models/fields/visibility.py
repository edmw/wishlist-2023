from typing import Any

from django.db import models

from ..types import Visibility


class VisibilityField(models.CharField):
    """Model field describing a wishlist’s visibility."""

    description = "Visibility of the wishlist"

    def __init__(self, *args: Any, **kwargs: Any):
        """Initializes the field as char field.

        Configures the field according to the properties of the visibility type.
        """
        kwargs["verbose_name"] = "Visibility"
        kwargs["help_text"] = self.description
        kwargs["db_column"] = "visibility"
        kwargs["max_length"] = Visibility.max_length
        kwargs["choices"] = Visibility.choices
        kwargs["null"] = False
        kwargs["blank"] = False
        kwargs["default"] = Visibility.default
        super().__init__(*args, **kwargs)
