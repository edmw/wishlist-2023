from typing import Protocol

from django.urls import reverse

from core import constants
from core.models._typing import HasPrimaryKey
from core.models.types import WishlistID
from core.models.wishlist import Wishlist


class HasWishlist(HasPrimaryKey, Protocol):
    wishlist_id: WishlistID
    wishlist: Wishlist


class WishURLsMixin:
    def get_absolute_edit_url(self: HasWishlist) -> str:
        """Returns the URL for the page to edit this wish.

        Returns:
            URL
        """
        return reverse(
            constants.VIEW_ITEM_UPDATE,
            kwargs={
                constants.USER_ID_KEY: self.wishlist.owner_id,
                constants.LIST_ID_KEY: self.wishlist_id,
                constants.ITEM_ID_KEY: self.pk,
            },
        )

    def get_absolute_manage_url(self: HasWishlist) -> str:
        """Returns the URL for the page to manage this wish.

        Returns:
            URL
        """
        return reverse(
            constants.VIEW_ITEM_MANAGE,
            kwargs={
                constants.USER_ID_KEY: self.wishlist.owner_id,
                constants.LIST_ID_KEY: self.wishlist_id,
                constants.ITEM_ID_KEY: self.pk,
            },
        )

    def get_absolute_move_url(self: HasWishlist) -> str:
        """Returns the URL for the page to move this wish.

        Returns:
            URL
        """
        return reverse(
            constants.VIEW_ITEM_MOVE,
            kwargs={
                constants.USER_ID_KEY: self.wishlist.owner_id,
                constants.LIST_ID_KEY: self.wishlist_id,
                constants.ITEM_ID_KEY: self.pk,
            },
        )

    def get_absolute_archive_url(self: HasWishlist) -> str:
        """Returns the URL for the page to archive this wish.

        Returns:
            URL
        """
        return reverse(
            constants.VIEW_ITEM_ARCHIVE,
            kwargs={
                constants.USER_ID_KEY: self.wishlist.owner_id,
                constants.LIST_ID_KEY: self.wishlist_id,
                constants.ITEM_ID_KEY: self.pk,
            },
        )

    def get_absolute_unarchive_url(self: HasWishlist) -> str:
        """Returns the URL for the page to unarchive this wish.

        Returns:
            URL
        """
        return reverse(
            constants.VIEW_ITEM_UNARCHIVE,
            kwargs={
                constants.USER_ID_KEY: self.wishlist.owner_id,
                constants.LIST_ID_KEY: self.wishlist_id,
                constants.ITEM_ID_KEY: self.pk,
            },
        )

    def get_absolute_release_url(self: HasWishlist) -> str:
        """Returns the URL for the page to release this wish.

        Returns:
            URL
        """
        return reverse(
            constants.VIEW_ITEM_RELEASE,
            kwargs={
                constants.USER_ID_KEY: self.wishlist.owner_id,
                constants.LIST_ID_KEY: self.wishlist_id,
                constants.ITEM_ID_KEY: self.pk,
            },
        )

    def get_absolute_receive_url(self: HasWishlist) -> str:
        """Returns the URL for the page to receive this wish.

        Returns:
            URL
        """
        return reverse(
            constants.VIEW_ITEM_RECEIVE,
            kwargs={
                constants.USER_ID_KEY: self.wishlist.owner_id,
                constants.LIST_ID_KEY: self.wishlist_id,
                constants.ITEM_ID_KEY: self.pk,
            },
        )

    def get_absolute_delete_url(self: HasWishlist) -> str:
        """Returns the URL for the page to delete this wish.

        Returns:
            URL
        """
        return reverse(
            constants.VIEW_ITEM_DELETE,
            kwargs={
                constants.USER_ID_KEY: self.wishlist.owner_id,
                constants.LIST_ID_KEY: self.wishlist_id,
                constants.ITEM_ID_KEY: self.pk,
            },
        )
