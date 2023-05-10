from typing import Any

from django.db import models

from ..types import ReferencePhoto


class ReferencePhotoField(models.URLField):
    """Model field describing a wish’s photo url reference."""

    description = "Reference Photo URL for a Wish"

    def __init__(self, *args: Any, **kwargs: Any):
        """Initializes the field as URL field.

        Configures the field according to the properties of the photo reference type.
        """
        kwargs["verbose_name"] = "Reference Photo URL"
        kwargs["help_text"] = self.description
        kwargs["db_column"] = "url_photo"
        kwargs["null"] = True
        kwargs["blank"] = True
        kwargs["max_length"] = ReferencePhoto.max_length
        super().__init__(*args, **kwargs)
