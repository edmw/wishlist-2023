from django.db import models

from ._uuid import UUIDFieldMixin


class InvitationIDField(UUIDFieldMixin, models.UUIDField):
    """Model field describing an invitation’s identifier."""

    description = "Unique ID of an invitation"
