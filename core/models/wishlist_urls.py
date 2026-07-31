from typing import Protocol

from django.urls import reverse

from core import constants
from core.models._typing import HasPrimaryKey
from core.models.types import UserID


class HasOwner(HasPrimaryKey, Protocol):
    owner_id: UserID


class URLMixin:
    def get_absolute_url(self: HasOwner) -> str:
        """Returns the URL for the page to view this wish list.

        Returns:
            URL
        """
        return reverse(
            constants.VIEW_WISHLIST,
            kwargs={constants.LIST_ID_KEY: self.pk},
        )

    def get_absolute_items_url(self: HasOwner) -> str:
        """Returns the URL for the page to view this wish list’s items.

        Returns:
            URL
        """
        return reverse(
            constants.VIEW_ITEMS,
            kwargs={
                constants.USER_ID_KEY: self.owner_id,
                constants.LIST_ID_KEY: self.pk,
            },
        )

    def get_absolute_memberships_url(self: HasOwner) -> str:
        """Returns the URL for the page to view this wish list’s memberships.

        Returns:
            URL
        """
        return reverse(
            constants.VIEW_MEMBERSHIPS,
            kwargs={
                constants.USER_ID_KEY: self.owner_id,
                constants.LIST_ID_KEY: self.pk,
            },
        )

    def get_absolute_edit_url(self: HasOwner) -> str:
        """Returns the URL for the page to edit this wish list.

        Returns:
            URL
        """
        return reverse(
            constants.VIEW_LIST_UPDATE,
            kwargs={
                constants.USER_ID_KEY: self.owner_id,
                constants.LIST_ID_KEY: self.pk,
            },
        )

    def get_absolute_delete_url(self: HasOwner) -> str:
        """Returns the URL for the page to delete this wish list.

        Returns:
            URL
        """
        return reverse(
            constants.VIEW_LIST_DELETE,
            kwargs={
                constants.USER_ID_KEY: self.owner_id,
                constants.LIST_ID_KEY: self.pk,
            },
        )

    def get_absolute_share_url(self: HasOwner) -> str:
        """Returns the URL for the page to share this wish list.

        Returns:
            URL
        """
        return reverse(
            constants.VIEW_LIST_SHARE,
            kwargs={
                constants.USER_ID_KEY: self.owner_id,
                constants.LIST_ID_KEY: self.pk,
            },
        )

    def get_absolute_export_url(self: HasOwner) -> str:
        """Returns the URL for the page to export this wish list.

        Returns:
            URL
        """
        return reverse(
            constants.VIEW_LIST_EXPORT,
            kwargs={
                constants.USER_ID_KEY: self.owner_id,
                constants.LIST_ID_KEY: self.pk,
            },
        )
