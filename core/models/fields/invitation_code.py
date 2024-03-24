from typing import Any

from django.db import models

from ..types import InvitationCode


class InvitationCodeField(models.CharField):
    """Model field describing an invitation code."""

    description = "Code for an invitation."

    def __init__(self, *args: Any, **kwargs: Any):
        """Initializes the field as char field.

        Configures the field according to the properties of the invitation code type.
        """
        kwargs["verbose_name"] = "Invitation code"
        kwargs["help_text"] = self.description
        kwargs["db_column"] = "invitation_code"
        kwargs["blank"] = True
        kwargs["max_length"] = InvitationCode.max_length
        super().__init__(*args, **kwargs)
