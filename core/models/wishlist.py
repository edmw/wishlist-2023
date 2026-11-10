"""Model class representing wish lists.

An entity that uses a name and description to represent a list of wishes for a
user. A wish list has a visibility for how it can be viewed by other users.
Items on a wish list have a sort order.
"""

import logging
from typing import TYPE_CHECKING, Any, Iterable, override

from django.conf import settings as django_settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.base import ModelBase
from django.utils.translation import gettext_lazy

from core.models import concerns, fields, types
from core.models._base import IDMixin
from core.models.types import Visibility

from .wishlist_types import TypesMixin
from .wishlist_urls import URLMixin

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from core.models.wish import Wish
    from core.models.wishlist_membership import WishlistMembership


class Wishlist(
    IDMixin[types.WishlistID],
    TypesMixin,
    URLMixin,
    concerns.Previewable,
    concerns.Captionable,
    models.Model,
):
    """Model used to represent a wishlist persisted in database."""

    MAXIMUM_NUMBER_OF_WISHLISTS_PER_USER = 100

    id_type = types.WishlistID
    id_field = fields.WishlistIDField()

    owner = models.ForeignKey(
        django_settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="wishlists"
    )
    owner_id: types.UserID

    name_field = fields.NameField()
    description_field = fields.DescriptionField()

    visibility_field = fields.VisibilityField()

    item_ordering_field = fields.ItemOrderingField()

    mask_reservations = models.BooleanField(default=False)

    # Relations

    wishes: models.QuerySet["Wish"]  # relation
    wishes_count: int  # annotation
    wishes_count_not_archived: int  # annotation

    collaboration_memberships: models.QuerySet["WishlistMembership"]  # relation

    # Lifecycle

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta data for the Wish list model."""

        verbose_name = "Wishlist"
        verbose_name_plural = "Wishlists"

    class Fields:
        """Field names for the Wish list model."""

        ID = "id_field"
        NAME = "name_field"
        DESCRIPTION = "description_field"
        WISHES = "wishes"
        OWNER = "owner"
        VISIBILITY = "visibility_field"
        ITEM_ORDERING = "item_ordering_field"
        MASK_RESERVATIONS = "mask_reservations"
        CREATED_AT = "created_at"
        MODIFIED_AT = "modified_at"

    # Concerns

    def __str__(self) -> str:
        """Returns a string representation of this wish list.

        Returns:
            Representation text.
        """
        return self.name

    def __repr__(self) -> str:
        """Returns a string reputation of this wish list.

        Returns:
            Reputation text.
        """
        return f"<{self.__class__.__name__}[{str(self.id)}]: {self.name}; owner={self.owner_id}>"

    @override
    def save(
        self,
        *args: Any,
        force_insert: bool | tuple[ModelBase, ...] = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Saves the current instance.

        If this save changes the visibility of an existing wish list to private,
        all open invitations of the list are revoked (see REQ-2.27/REQ-2.28). The
        hook lives on the model so that every path — form, admin, or a future
        service — is covered; switching between the other visibilities has no
        effect on invitations (see REQ-2.29).
        """
        self.full_clean()

        becomes_private = False
        if self.pk and self.visibility == Visibility.PRIVATE:
            if update_fields is None or Wishlist.Fields.VISIBILITY in update_fields:
                current_visibility = (
                    Wishlist.objects.filter(pk=self.pk)
                    .values_list(Wishlist.Fields.VISIBILITY, flat=True)
                    .first()
                )
                becomes_private = current_visibility != Visibility.PRIVATE

        super().save(
            *args,
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
            **kwargs,
        )

        if becomes_private:
            from core.services import InvitationService

            InvitationService.revoke_pending_for_wishlist(wishlist=self)

    @override
    def captionable(self) -> str:
        """Returns a caption text for this wish list.

        Returns:
           Caption text.
        """
        return self.name

    def previewable(self) -> str:
        """Returns a preview text for this wish list.

        Returns:
            Preview text.
        """
        return self.description

    @property
    def is_shareable(self) -> bool:
        """Whether this wish list can be shared by invitation.

        Private wish lists are never shared by invitation (see ADR-1000).

        Returns:
            True if the visibility allows sharing, False otherwise.
        """
        return self.visibility != Visibility.PRIVATE

    def clean(self) -> None:
        super().clean()

        if self.pk and self.visibility == Visibility.PRIVATE:
            current_visibility = (
                Wishlist.objects.filter(pk=self.pk)
                .values_list(Wishlist.Fields.VISIBILITY, flat=True)
                .first()
            )
            if current_visibility != Visibility.PRIVATE and self.collaboration_memberships.exists():
                raise ValidationError(
                    {
                        Wishlist.Fields.VISIBILITY: gettext_lazy(
                            'Visibility cannot be changed to "Only you" '
                            "while editors still have access to this list."
                        )
                    }
                )
