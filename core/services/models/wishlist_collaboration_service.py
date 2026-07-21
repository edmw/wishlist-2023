"""Wishlist collaboration services."""

import logging

from core.models import User, Wishlist, WishlistMembership
from core.models.types import Visibility, WishlistMembershipRole

logger = logging.getLogger(__name__)


class WishlistCollaborationServiceError(Exception):
    pass


class WishlistCollaborationPrivateWishlistError(WishlistCollaborationServiceError):
    pass


class WishlistCollaborationOwnerAsEditorError(WishlistCollaborationServiceError):
    pass


class WishlistCollaborationService:
    """Service for managing collaboration memberships on wishlists."""

    @staticmethod
    def is_editor(*, wishlist: Wishlist, user: User) -> bool:
        return WishlistMembership.objects.filter(
            wishlist=wishlist,
            user=user,
            role_field=WishlistMembershipRole.EDITOR,
        ).exists()

    @staticmethod
    def add_editor(*, wishlist: Wishlist, user: User) -> bool:
        if wishlist.visibility == Visibility.PRIVATE:
            raise WishlistCollaborationPrivateWishlistError()

        if wishlist.owner_id == user.id:
            raise WishlistCollaborationOwnerAsEditorError()

        _, created = WishlistMembership.objects.get_or_create(
            wishlist=wishlist,
            user=user,
            defaults={WishlistMembership.Fields.ROLE: WishlistMembershipRole.EDITOR},
        )
        return created

    @staticmethod
    def remove_editor(*, wishlist: Wishlist, user: User) -> bool:
        deleted_count, _ = WishlistMembership.objects.filter(
            wishlist=wishlist,
            user=user,
            role_field=WishlistMembershipRole.EDITOR,
        ).delete()
        return deleted_count > 0
