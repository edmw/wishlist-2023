from typing import Any

from django.db import models

from ..types import InvitationEmail


class InvitationEmailField(models.EmailField):
    """Model field describing the email address of an invitation’s invitee."""

    description = "The email address of the user this invitation is intended for."

    def __init__(self, *args: Any, **kwargs: Any):
        """Initializes the field as email field.

        Configures the field according to the properties of the invitation
        email type.
        """
        kwargs["verbose_name"] = "Invitee email"
        kwargs["help_text"] = self.description
        kwargs["db_column"] = "invitee_email"
        kwargs["blank"] = False
        kwargs["max_length"] = InvitationEmail.max_length
        super().__init__(*args, **kwargs)
