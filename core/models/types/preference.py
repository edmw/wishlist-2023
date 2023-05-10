from django.utils.translation import gettext_lazy


class Preference(int):
    """Model field type for a wish’s preference.

    Specifies the valid choices for the preference text and a default.
    """

    LOWEST = -2
    LOW = -1
    NEUTRAL = 0
    HIGH = 1
    HIGHEST = 2

    PREFERENCES = [
        (LOWEST, gettext_lazy("Not so important")),
        (LOW, gettext_lazy("Not so sure")),
        (NEUTRAL, gettext_lazy("Would be happy")),
        (HIGH, gettext_lazy("Would love to have")),
        (HIGHEST, gettext_lazy("Must have")),
    ]
    PREFERENCES_DICT = dict(PREFERENCES)

    choices = PREFERENCES
    default = 0

    @property
    def display(self) -> str:
        """Returns a string that can be used for display in the UI.

        The returned string is not localized.

        Returns:
            String for display use.
        """
        return self.PREFERENCES_DICT.get(self, "")
