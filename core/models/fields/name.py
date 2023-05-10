from typing import Any

from django.core.validators import MinLengthValidator
from django.db import models

from ..types import Name


class NameField(models.CharField):
    """Model field describing a wish’s or a wishlist’s name."""

    description = "Name of a Wishlist or a Wish"

    def __init__(self, *args: Any, **kwargs: Any):
        """Initializes the field as char field.

        Configures the field according to the properties of the name type.
        """
        kwargs["verbose_name"] = "Name"
        kwargs["help_text"] = self.description
        kwargs["db_column"] = "name"
        kwargs["blank"] = False
        kwargs["max_length"] = Name.max_length
        kwargs["validators"] = [MinLengthValidator(Name.min_length)]
        super().__init__(*args, **kwargs)
