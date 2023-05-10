from typing import Any

from django.db import models

from ..types import Description


class DescriptionField(models.CharField):
    """Model field describing a wish’s or a wishlist’s description."""

    description = "Description of a Wishlist or a Wish"

    def __init__(self, *args: Any, **kwargs: Any):
        """Initializes the field as char field.

        Configures the field according to the properties of the description type.
        """
        kwargs["verbose_name"] = "Description"
        kwargs["help_text"] = self.description
        kwargs["db_column"] = "description"
        kwargs["blank"] = True
        kwargs["max_length"] = Description.max_length
        super().__init__(*args, **kwargs)
