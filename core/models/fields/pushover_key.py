from typing import Any

from django.db import models

from ..types import PushoverKey


class PushoverKeyField(models.CharField):
    """Model field describing a key to access Pushover."""

    description = "Key to access Pushover."

    def __init__(self, *args: Any, **kwargs: Any):
        """Initializes the field as char field.

        Configures the field according to the properties of the pushover key type.
        """
        kwargs["verbose_name"] = "Pushover key"
        kwargs["help_text"] = self.description
        kwargs["db_column"] = "pushover_key"
        kwargs["blank"] = True
        kwargs["max_length"] = PushoverKey.max_length
        super().__init__(*args, **kwargs)
