from typing import Any

from django.db import models

from ..types import ItemOrdering


class ItemOrderingField(models.CharField):
    """Model field describing a wishlist’s items ordering."""

    description = "Ordering of the items of the wishlist"

    def __init__(self, *args: Any, **kwargs: Any):
        """Initializes the field as char field.

        Configures the field according to the properties of the ordering type.
        """
        kwargs["verbose_name"] = "Item Ordering"
        kwargs["help_text"] = self.description
        kwargs["db_column"] = "item_ordering"
        kwargs["max_length"] = ItemOrdering.max_length
        kwargs["choices"] = ItemOrdering.choices
        kwargs["null"] = False
        kwargs["blank"] = False
        kwargs["default"] = ItemOrdering.default
        super().__init__(*args, **kwargs)
