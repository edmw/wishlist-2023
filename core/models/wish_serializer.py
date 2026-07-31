from rest_framework import serializers

from .wish import Wish


class WishSerializer(serializers.ModelSerializer):
    class Meta:  # type: ignore[override]
        model = Wish
        exclude = [
            Wish.Fields.ID,
            Wish.Fields.NAME,
            Wish.Fields.DESCRIPTION,
            Wish.Fields.REFERENCE,
            Wish.Fields.REFERENCE_PHOTO,
            Wish.Fields.PREFERENCE,
            Wish.Fields.IMAGE,
            Wish.Fields.WISHLIST,
        ]

    name = serializers.CharField(source=Wish.Fields.NAME)
    description = serializers.CharField(source=Wish.Fields.DESCRIPTION)
    reference = serializers.CharField(source=Wish.Fields.REFERENCE)
    reference_photo = serializers.CharField(source=Wish.Fields.REFERENCE_PHOTO)
    preference = serializers.CharField(source=Wish.Fields.PREFERENCE)
