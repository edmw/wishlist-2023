from core.models import User, Wishlist, types


class WishlistFactory:
    @classmethod
    def create(
        cls,
        id: types.WishlistID,
        name: types.Name,
        description: types.Description,
        owner: User,
        visibility: types.Visibility,
        item_ordering: types.ItemOrdering,
        mask_reservations: bool,
    ) -> Wishlist:
        """Create a wish list model instance without persisting it.

        Arguments:
            id: The identifier for the new wish list.
            name: Name for the new wish list.
            description: Description for the new wish list.
            owner: Owner of the new wish list.
            visibility: Visibility for the new wish list.
            item_ordering: Order of items for the new wish list.
            mask_reservations: Reservation masking for the new wish list.

        Returns:
            Wish list instance created.
        """
        return Wishlist(
            id_field=id,
            name_field=name,
            description_field=description,
            owner=owner,
            visibility_field=visibility,
            item_ordering_field=item_ordering,
            mask_reservations=mask_reservations,
        )
