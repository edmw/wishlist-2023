from datetime import datetime

from core.models import Wish, Wishlist, types


class WishFactory:
    @classmethod
    def create(
        cls,
        id: types.WishID,
        name: types.Name,
        description: types.Description,
        reference: types.Reference,
        reference_photo: types.ReferencePhoto,
        preference: types.Preference,
        wishlist: Wishlist,
        archived: bool,
        archived_at: datetime | None,
    ) -> Wish:
        """Create a wish model instance without persisting it.

        Arguments:
            id: The identifier for the new wish.
            name: Name for the new wish.
            description: Description for the new wish.
            reference: Web reference for the new wish.
            reference_photo: Web reference to photo for the new wish.
            preference: Preference for the new wish.
            wishlist: Wishlist this new wish belongs to.
            archived: Flag, indicating if this new wish is archived.
            archived_at: Date when this new wish was archived.

        Returns:
            Wish instance created.
        """
        return Wish(
            id_field=id,
            name_field=name,
            description_field=description,
            reference_field=reference,
            reference_photo_field=reference_photo,
            preference_field=preference,
            wishlist=wishlist,
            archived=archived,
            archived_at=archived_at,
        )
