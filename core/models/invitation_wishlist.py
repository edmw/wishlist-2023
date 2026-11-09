"""Model class representing an invitation to a wishlist."""

import logging
from typing import override

from django.db import models

from core.models import fields, types
from core.models.invitation import Invitation
from core.models.invitation_expirable import ExpiresAfterFixedTime
from core.models.invitation_urls import InvitationURLsMixin
from core.models.wishlist import Wishlist

logger = logging.getLogger(__name__)


class WishlistInvitation(ExpiresAfterFixedTime, Invitation, InvitationURLsMixin):
    """Model used to represent an invitation to a wishlist persisted in database.

    An invitation has exactly one variant: `NOTIFY` only makes the wish list
    known to the recipient, while `EDITOR` additionally offers them to become
    an editor of the list (see REQ-2.2). Accepting the invitation does not
    grant any additional access; invitations can only be sent for wish lists
    that are visible to all users or publicly, so the invitee's access stays
    bound to the visibility of the list (see ADR-1000).
    """

    EXPIRES_AFTER_SETTINGS_KEY = "WISHLIST_INVITATION_EXPIRES_AFTER"

    # Relations

    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, blank=False, null=False)
    wishlist_id: types.WishlistID | None

    variant_field = fields.InvitationVariantField()

    class Meta:  # type: ignore[override]
        """Meta data for the WishlistInvitation model."""

        verbose_name = "Wishlist Invitation"
        verbose_name_plural = "Wishlist Invitations"

    class Fields(Invitation.Fields):
        """Field names for the WishlistInvitation model."""

        WISHLIST = "wishlist"
        VARIANT = "variant_field"

    # Properties

    @property
    def variant(self) -> types.InvitationVariant:
        """The variant of this invitation. This computed property returns the
        correctly typed value instead of an indeterminate string.

        Returns:
            The variant of the invitation.
        """
        return types.InvitationVariant(self.variant_field)

    @variant.setter
    def variant(self, variant: types.InvitationVariant) -> None:
        """The setter for the variant of this invitation. This custom setter
        accepts a correctly typed value, only, instead of an indeterminate
        string.

        Arguments:
            variant: The variant of the invitation.
        """
        self.variant_field = str(variant)

    # Custom methods

    @override
    def was_accepted(self) -> None:
        """Called after this invitation has been accepted.

        Accepting a wishlist invitation does not grant any additional access;
        access to the list is already covered by its visibility, so only the
        status of the invitation changes (handled by the caller).
        """
        logger.debug("WishlistInvitation %s was accepted.", self.id)
