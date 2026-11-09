from typing import Any

from django.db import models

from ..types import InvitationVariant


class InvitationVariantField(models.CharField):
    """Model field describing the variant of an invitation."""

    description = "The variant of the invitation (notify or notify and editor)."

    def __init__(self, *args: Any, **kwargs: Any):
        """Initializes the field as char field.

        Configures the field according to the properties of the invitation
        variant type.
        """
        kwargs["verbose_name"] = "Variant"
        kwargs["help_text"] = self.description
        kwargs["db_column"] = "variant"
        kwargs["max_length"] = InvitationVariant.max_length
        kwargs["choices"] = InvitationVariant.choices
        kwargs["null"] = False
        kwargs["blank"] = False
        kwargs["default"] = InvitationVariant.default
        super().__init__(*args, **kwargs)
