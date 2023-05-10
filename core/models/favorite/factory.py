from core.models import Favorite, User, Wishlist, types


class FavoriteFactory:
    @classmethod
    def create(
        cls,
        id: types.FavoriteID,
        user: User,
        wishlist: Wishlist,
        notify_on_item_create: bool,
    ) -> Favorite:
        """Create a favorite model instance without persisting it.

        Arguments:
            id: The identifier for the new favorite.
            user: User of the new favorite.
            wishlist: List of the new favorite.
            notify_on_item_create: Notifications for the new favorite.

        Returns:
            Favorite instance created.
        """
        return Favorite(
            id_field=id,
            user=user,
            wishlist=wishlist,
            notify_on_item_create=notify_on_item_create,
        )
