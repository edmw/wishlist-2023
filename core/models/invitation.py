"""Model class representing a general invitation."""
from __future__ import annotations

import logging

from django.conf import settings as django_settings
from django.db import models

from core.models import fields, types
from core.models._base import IDMixin

logger = logging.getLogger(__name__)


class Invitation(
    IDMixin[types.InvitationID],
    models.Model,
):
    """Abstract model used to represent a general reservation persisted in
    database.
    """

    id_type = types.InvitationID
    id_field = fields.InvitationIDField()

    inviter = models.ForeignKey(
        django_settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="invitations"
    )
    inviter_id: types.UserID

    # Lifecycle

    created_at = models.DateTimeField(auto_now_add=True)

    sent = models.BooleanField(
        default=False,
        verbose_name="sent",
        help_text=(
            "Indicates whether this invitation has been sent to the invitee."
        ),
    )
    sent_at = models.DateTimeField(blank=True, null=True)

    accepted = models.BooleanField(
        default=False,
        verbose_name="accepted",
        help_text=(
            "Indicates whether this invitation has been accepted by the invitee."
        ),
    )
    accepted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        """Meta data for the abstract Invitation model."""

        abstract = True

        verbose_name = "Invitation"
        verbose_name_plural = "Invitations"

    class Fields:
        """Field names for the Invitation model."""

        ID = "id_field"
        INVITER = "inviter"
        CREATED_AT = "created_at"
        SENT = "sent"
        SENT_AT = "sent_at"
        ACCEPTED = "accepted"
        ACCEPTED_AT = "accepted_at"

    # Concerns

    def __str__(self) -> str:
        """Returns a string representation of this invitation.

        Returns:
            Representation text.
        """
        return f"{self.inviter_id}"

    def __repr__(self) -> str:
        """Returns a string reputation of this reservation.

        Returns:
            Reputation text.
        """
        return f"<{self.__class__.__name__}[{str(self.id)}]: inviter={self.inviter_id};>"

    # Custom properties

    @property
    def expired(self) -> bool:
        # Indicates whether this invitation has been expired after sending.
        raise NotImplementedError("The expired property must be implemented!")

    # Custom methods

    def was_accepted(self) -> None:
        # A function called after this invitation has been accepted.
        raise NotImplementedError("The was_accepted method must be implemented!")
