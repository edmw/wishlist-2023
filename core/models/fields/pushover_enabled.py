from typing import Any

from django.db import models


class PushoverEnabledField(models.BooleanField):
    """Model field describing a flag for pushover notifications."""

    description = "Designates whether a user wants to receive notifications by Pushover."

    def __init__(self, *args: Any, **kwargs: Any):
        """Initializes the field as boolean field."""
        kwargs["verbose_name"] = "Pushover notifications enabled"
        kwargs["help_text"] = self.description
        kwargs["db_column"] = "pushover_enabled"
        kwargs["blank"] = True
        kwargs["default"] = False
        super().__init__(*args, **kwargs)
