from typing import Any

from django.db import models

from ..types import InvitationState


class InvitationStateField(models.CharField):
    """Model field describing the state of an invitation."""

    description = "The current state of the invitation."

    def __init__(self, *args: Any, **kwargs: Any):
        """Initializes the field as char field.

        Configures the field according to the properties of the invitation
        state type. Only the stored states are offered as choices; `EXPIRED`
        is derived at read time and must never be written.
        """
        kwargs["verbose_name"] = "State"
        kwargs["help_text"] = self.description
        kwargs["db_column"] = "state"
        kwargs["max_length"] = InvitationState.max_length
        kwargs["choices"] = InvitationState.choices
        kwargs["null"] = False
        kwargs["blank"] = False
        kwargs["default"] = InvitationState.default
        super().__init__(*args, **kwargs)
