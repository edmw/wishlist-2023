"""Model class representing an invitation to a wishlist."""
import logging

from django.db import models

from core.models import types
from core.models.invitation import Invitation
from core.models.wishlist import Wishlist

logger = logging.getLogger(__name__)


class WishlistInvitation(Invitation):
    # Relations

    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, blank=False, null=False)
    wishlist_id: types.WishlistID | None
