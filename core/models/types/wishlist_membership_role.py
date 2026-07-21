from django.utils.translation import gettext_lazy


class WishlistMembershipRole(str):
    """Model field type for a wishlist membership role."""

    EDITOR = "editor"

    ROLES = [
        (EDITOR, gettext_lazy("Editor")),
    ]
    ROLES_DICT = dict(ROLES)

    max_length = 32
    choices = ROLES
    default = EDITOR

    @property
    def display(self) -> str:
        """Returns a string that can be used for display in the UI."""
        return self.ROLES_DICT.get(self, "")
