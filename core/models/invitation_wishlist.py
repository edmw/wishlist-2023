"""Model class representing an invitation to a wishlist."""

import logging
from typing import override

from django.db import models

from core.models import types
from core.models.invitation import Invitation
from core.models.invitation_expirable import ExpiresAfterFixedTime
from core.models.wishlist import Wishlist

logger = logging.getLogger(__name__)


class WishlistInvitation(ExpiresAfterFixedTime, Invitation):
    """Model used to represent an invitation to a wishlist persisted in database.

    Accepting the invitation does not grant any additional access: invitations
    can only be sent for wish lists that are visible to all users or publicly,
    so the invitee's access stays bound to the visibility of the list (see
    ADR-1000).
    """

    EXPIRES_AFTER_SETTINGS_KEY = "WISHLIST_INVITATION_EXPIRES_AFTER"

    # Relations

    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, blank=False, null=False)
    wishlist_id: types.WishlistID | None

    class Meta:  # type: ignore[override]
        """Meta data for the WishlistInvitation model."""

        verbose_name = "Wishlist Invitation"
        verbose_name_plural = "Wishlist Invitations"

    class Fields(Invitation.Fields):
        """Field names for the WishlistInvitation model."""

        WISHLIST = "wishlist"

    # Custom methods

    @override
    def was_accepted(self) -> None:
        """Called after this invitation has been accepted.

        Accepting a wishlist invitation does not create any membership or
        grant additional rights; access to the list is already covered by its
        visibility, so only the status of the invitation changes (handled by
        the caller).
        """
        logger.debug("WishlistInvitation %s was accepted.", self.id)
