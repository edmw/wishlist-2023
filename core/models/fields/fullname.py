from typing import Any

from django.db import models

from ..types import Fullname


class FullnameField(models.CharField):
    """Model field describing a user’s full name."""

    description = "Full name of a user"

    def __init__(self, *args: Any, **kwargs: Any):
        """Initializes the field as char field.

        Configures the field according to the properties of the full name type.
        """
        kwargs["verbose_name"] = "Full name"
        kwargs["db_column"] = "full_name"
        kwargs["blank"] = True
        kwargs["max_length"] = Fullname.max_length
        super().__init__(*args, **kwargs)
