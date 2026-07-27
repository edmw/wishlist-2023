"""Model class representing wishes.

An entity that uses a Name, Description, and reference to a web page or photo
to describe a wish on a wish list. A wish has a priority for how much it is
wanted.
"""

from __future__ import annotations

from django.db import models

from core.models import Reservation, concerns, fields, types
from core.models._base import IDMixin

from .wish_on_save_generate_image import OnSaveGenerateImageMixin
from .wish_on_save_notify import OnSaveNotifyMixin
from .wish_types import WishTypesMixin
from .wish_urls import WishURLsMixin


class Wish(
    IDMixin[types.WishID],
    WishTypesMixin,
    WishURLsMixin,
    OnSaveGenerateImageMixin,
    OnSaveNotifyMixin,
    concerns.Previewable,
    models.Model,
):
    """Model used to represent a wish persisted in database."""

    MAXIMUM_NUMBER_OF_WISHES_PER_WISHLIST = 100

    id_type = types.WishID
    id_field = fields.WishIDField()

    name_field = fields.NameField()

    description_field = fields.DescriptionField()

    reference_field = fields.ReferenceField()
    reference_photo_field = fields.ReferencePhotoField()

    preference_field = fields.PreferenceField()

    image_field = fields.WishImageField()

    # Relations

    wishlist = models.ForeignKey(
        "Wishlist", on_delete=models.CASCADE, blank=False, null=False, related_name="wishes"
    )
    wishlist_id: types.WishlistID | None

    reservation: Reservation

    # Lifecycle

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        """Meta data for the Wish model."""

        verbose_name = "Wish"
        verbose_name_plural = "Wishes"

    class Fields:
        """Field names for the Wish model."""

        ID = "id_field"
        NAME = "name_field"
        DESCRIPTION = "description_field"
        REFERENCE = "reference_field"
        REFERENCE_PHOTO = "reference_photo_field"
        PREFERENCE = "preference_field"
        IMAGE = "image_field"
        WISHLIST = "wishlist"
        CREATED_AT = "created_at"
        MODIFIED_AT = "modified_at"
        ARCHIVED = "archived"
        ARCHIVED_AT = "archived_at"

    # Concerns

    def __str__(self) -> str:
        """Returns a string representation of this wish.

        Returns:
            Representation text.
        """
        return self.name

    def __repr__(self) -> str:
        """Returns a string reputation of this wish list.

        Returns:
            Reputation text.
        """
        return f"<{self.__class__.__name__}[{str(self.id)}]: {self.name}; list={self.wishlist_id}>"

    def previewable(self) -> str:
        """Returns a preview text for this wish.

        Returns:
            Preview text.
        """
        return self.description

    # Custom properties

    def get_reservation(self) -> Reservation | None:
        try:
            return self.reservation
        except Reservation.DoesNotExist:
            return None

    @property
    def reservable(self) -> bool:
        # A wish can be reserved if there is no reservation
        # and the wish is not archived.
        return self.get_reservation() is None and not self.archived

    @property
    def is_reserved(self) -> bool:
        # A wish is reserved if there is a reservation.
        return self.get_reservation() is not None

    @property
    def receivable(self) -> bool:
        # A wish can be received if there is a reservation
        # and the reservation is not completed.
        if reservation := self.get_reservation():
            return not reservation.completed and not self.archived
        else:
            return False

    @property
    def is_received(self) -> bool:
        # A wish is received if there is a reservation
        # and the reservation is completed.
        if reservation := self.get_reservation():
            return reservation.completed
        else:
            return False

    @property
    def archivable(self) -> bool:
        # A wish can be archived if the wish is not archived
        # and there is either no reservation
        # or the reservation is completed.
        return not self.archived and (not self.is_reserved or self.is_received)

    @property
    def is_archived(self) -> bool:
        # A wish is archived if it is archived.
        return self.archived

    @property
    def movable(self) -> bool:
        # A wish can be moved if there is either no reservation
        # or the reservation is completed.
        return not self.is_reserved or self.is_received

    @property
    def deletable(self) -> bool:
        # A wish can be deleted if there is either no reservation
        # or the reservation is completed.
        return not self.is_reserved or self.is_received
