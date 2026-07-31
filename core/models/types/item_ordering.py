from django.utils.translation import gettext_lazy


class ItemOrdering(str):
    """Model field type for a wishlist’s items ordering.

    Specifies the valid choices for the ordering text and a default.
    """

    NAME_ASCENDING = "+name"
    NAME_DESCENDING = "-name"
    PREFERENCE_ASCENDING = "+preference"
    PREFERENCE_DESCENDING = "-preference"
    CREATED_AT_ASCENDING = "+created_at"
    CREATED_AT_DESCENDING = "-created_at"
    MODIFIED_AT_ASCENDING = "+modified_at"
    MODIFIED_AT_DESCENDING = "-modified_at"

    ITEM_ORDERINGS = [
        (NAME_ASCENDING, gettext_lazy("Name (ascending)")),
        (NAME_DESCENDING, gettext_lazy("Name (descending)")),
        (PREFERENCE_ASCENDING, gettext_lazy("Preference (ascending)")),
        (PREFERENCE_DESCENDING, gettext_lazy("Preference (descending)")),
        (CREATED_AT_ASCENDING, gettext_lazy("Added at (ascending)")),
        (CREATED_AT_DESCENDING, gettext_lazy("Added at (descending)")),
        (MODIFIED_AT_ASCENDING, gettext_lazy("Modified at (ascending)")),
        (MODIFIED_AT_DESCENDING, gettext_lazy("Modified at (descending)")),
    ]
    ITEM_ORDERINGS_DICT = dict(ITEM_ORDERINGS)

    max_length = 16
    choices = ITEM_ORDERINGS
    default = "+name"

    @property
    def display(self) -> str:
        """Returns a string that can be used for display in the UI.

        Returns:
            String for display use.
        """
        return str(self.ITEM_ORDERINGS_DICT.get(self, ""))
