from django.utils.translation import gettext_lazy


class Visibility(str):
    """Model field type for a wishlist’s visibility.

    Specifies the valid choices for the visibility text and a default.
    """

    PRIVATE = "private"
    USERS = "users"
    PUBLIC = "public"

    VISIBILITIES = [
        (PRIVATE, gettext_lazy("Only you")),
        (USERS, gettext_lazy("All users")),
        (PUBLIC, gettext_lazy("Public")),
    ]
    VISIBILITIES_DICT = dict(VISIBILITIES)

    max_length = 16
    choices = VISIBILITIES
    default = "private"

    @property
    def display(self) -> str:
        """Returns a string that can be used for display in the UI.

        The returned string is not localized.

        Returns:
            String for display use.
        """
        return self.VISIBILITIES_DICT.get(self, "")
