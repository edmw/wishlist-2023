import logging
from typing import Any

import yaml

from core.models import Wish, Wishlist, WishlistSerializer, WishSerializer

logger = logging.getLogger(__name__)


class SerializationService:
    @classmethod
    def item_to_dict(cls, *, wish: Wish) -> dict[str, Any]:
        return dict(WishSerializer(wish).data)

    @classmethod
    def list_to_dict(cls, *, wishlist: Wishlist) -> dict[str, Any]:
        result = dict(WishlistSerializer(wishlist).data)
        wishes = []
        for wish in wishlist.wishes.all():
            wishes.append(cls.item_to_dict(wish=wish))
        result[Wishlist.Fields.WISHES] = wishes
        return {"wishlist": result}

    @staticmethod
    def wishlist_yaml(*, wishlist: Wishlist) -> str:
        data = SerializationService.list_to_dict(wishlist=wishlist)
        export = {"version": "wishlist/1", "data": data}
        return yaml.dump(
            export,
            sort_keys=False,
            explicit_start=True,
            default_flow_style=False,
        )
