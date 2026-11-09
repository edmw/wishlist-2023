from django.utils.translation import gettext_lazy


class InvitationVariant(str):
    """Model field type for the variant of an invitation.

    Specifies the valid variants and a default. `NOTIFY` only makes the wish
    list known to the recipient; `EDITOR` additionally offers them to become
    an editor of the list.
    """

    NOTIFY = "notify"
    EDITOR = "editor"

    VARIANTS = [
        (NOTIFY, gettext_lazy("Notify")),
        (EDITOR, gettext_lazy("Notify and editor")),
    ]
    VARIANTS_DICT = dict(VARIANTS)

    max_length = 16
    choices = VARIANTS
    default = NOTIFY

    @property
    def display(self) -> str:
        """Returns a string that can be used for display in the UI.

        Returns:
            String for display use.
        """
        return str(self.VARIANTS_DICT.get(self, ""))
