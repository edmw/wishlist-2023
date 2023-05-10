"""Context services for views.

A set of request processors that return dictionaries to be merged into a
template context. Each function takes the request object as its only parameter
and returns a dictionary to add to the context.
"""
from django.http import HttpRequest

from core.apps import CoreConfig
from core.models import Favorite, Wish, Wishlist


def settings(request: HttpRequest) -> dict:
    """Context request processor that provides the Core’s settings."""
    return {
        "core": {
            "access": CoreConfig.access,
            "contact_name": CoreConfig.contact_name,
            "contact_address": CoreConfig.contact_address,
            "contact_email": CoreConfig.contact_email,
            "contact_phone": CoreConfig.contact_phone,
            "maximum_number_of_wishlists_per_user": Wishlist.MAXIMUM_NUMBER_OF_WISHLISTS_PER_USER,
            "maximum_number_of_wishes_per_wishlist": Wish.MAXIMUM_NUMBER_OF_WISHES_PER_WISHLIST,
            "maximum_number_of_favorites_per_user": Favorite.MAXIMUM_NUMBER_OF_FAVORITES_PER_USER,
        },
    }


def constants(request: HttpRequest) -> dict:
    """Context request processor that provides the Core’s constants."""
    from core import constants

    return {
        "user_id_key": constants.USER_ID_KEY,
        "list_id_key": constants.LIST_ID_KEY,
        "item_id_key": constants.ITEM_ID_KEY,
        "favorite_id_key": constants.FAVORITE_ID_KEY,
        "reservation_id_key": constants.RESERVATION_ID_KEY,
    }
