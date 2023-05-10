class Language(str):
    """Model field type for a user’s language.

    Specifies the valid choices for the language text and a default.
    """

    LANGUAGES = [
        ("", "-"),
        ("en", "English"),
        ("de", "Deutsch"),
    ]
    LANGUAGES_DICT = dict(LANGUAGES)

    max_length = 2
    choices = LANGUAGES
    default = ""

    @property
    def display(self) -> str:
        """Returns a string that can be used for display in the UI.

        The returned string is not localized. In this special case (name of a
        language) the returned string is translated into the language it is
        intended to represent.

        Returns:
            String for display use.
        """
        return self.LANGUAGES_DICT.get(self, "")

    def get_code(self) -> str:
        return str(self) or "en"
