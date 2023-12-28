from rest_framework import serializers

from .wishlist import Wishlist


class WishlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        exclude = [
            Wishlist.Fields.ID,
            Wishlist.Fields.NAME,
            Wishlist.Fields.DESCRIPTION,
            Wishlist.Fields.VISIBILITY,
            Wishlist.Fields.ITEM_ORDERING,
            Wishlist.Fields.OWNER,
        ]

    name = serializers.CharField(source=Wishlist.Fields.NAME)
    description = serializers.CharField(source=Wishlist.Fields.DESCRIPTION)
    visibility = serializers.CharField(source=Wishlist.Fields.VISIBILITY)
    item_ordering = serializers.CharField(source=Wishlist.Fields.ITEM_ORDERING)
