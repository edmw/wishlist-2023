from typing import Any

from django.db import models

from ..types import Reference


class ReferenceField(models.URLField):
    """Model field describing a wish’s url reference."""

    description = "Reference URL for a Wish"

    def __init__(self, *args: Any, **kwargs: Any):
        """Initializes the field as URL field.

        Configures the field according to the properties of the reference type.
        """
        kwargs["verbose_name"] = "Reference URL"
        kwargs["help_text"] = self.description
        kwargs["db_column"] = "url"
        kwargs["null"] = True
        kwargs["blank"] = True
        kwargs["max_length"] = Reference.max_length
        super().__init__(*args, **kwargs)
