from core.models.types import Description, Name, Preference, Reference, ReferencePhoto


class WishTypesMixin:
    @property
    def name(self) -> Name:
        """The name for this wish. This computed property returns the
        correctly typed value instead of an indeterminate string.

        Returns:
            The name.
        """
        return Name(self.name_field)

    @name.setter
    def name(self, name: Name) -> None:
        """The setter for the name of this wish. This custom setter
        accepts a correctly typed value, only, instead of an indeterminate
        string.

        Arguments:
            name: The name.
        """
        self.name_field = name

    @property
    def description(self) -> Description:
        """The description for this wish. This computed property returns the
        correctly typed value instead of an indeterminate string.

        Returns:
            The description.
        """
        return Description(self.description_field)

    @description.setter
    def description(self, description: Description) -> None:
        """The setter for the description of this wish. This custom setter
        accepts a correctly typed value, only, instead of an indeterminate
        string.

        Arguments:
            description: The description.
        """
        self.description_field = description

    @property
    def reference(self) -> Reference | None:
        """The web reference for this wish. This computed property returns the
        correctly typed value instead of an indeterminate url.

        Returns:
            The reference.
        """
        if not self.reference_field:
            return None
        return Reference(self.reference_field)

    @reference.setter
    def reference(self, reference: Reference) -> None:
        """The setter for the web reference of this wish. This custom setter
        accepts a correctly typed value, only, instead of an indeterminate
        url.

        Arguments:
            reference: The reference.
        """
        self.reference_field = reference

    @property
    def reference_photo(self) -> ReferencePhoto | None:
        """The web reference to an photo for this wish. This computed property
        returns the correctly typed value instead of an indeterminate url.

        Returns:
            The reference to a photo.
        """
        if not self.reference_photo_field:
            return None
        return ReferencePhoto(self.reference_photo_field)

    @reference_photo.setter
    def reference_photo(self, reference_photo: ReferencePhoto) -> None:
        """The setter for the web reference for an photo of this wish. This
        custom setter accepts a correctly typed value, only, instead of an
        indeterminate string.

        Arguments:
            reference_photo: The reference to a photo.
        """
        self.reference_photo_field = reference_photo

    @property
    def preference(self) -> Preference:
        """The preference for this wish. This computed property returns the
        correctly typed value instead of an indeterminate string.

        Returns:
            A value from the Preference choices.
        """
        return Preference(self.preference_field)

    @preference.setter
    def preference(self, preference: Preference) -> None:
        """The setter for the preference of this wish list. This custom setter
        accepts a correctly typed value, only, instead of an indeterminate
        string.

        Arguments:
            preference: A value from the Preference choices.
        """
        self.preference_field = preference
