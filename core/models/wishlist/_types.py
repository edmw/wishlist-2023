from core.models.types import Description, ItemOrdering, Name, Visibility


class TypesMixin:
    @property
    def name(self) -> Name:
        """The name for this wish list. This computed property returns the
        correctly typed value instead of an indeterminate string.

        Returns:
            The name.
        """
        return Name(self.name_field)

    @name.setter
    def name(self, name: Name) -> None:
        """The setter for the name of this wish list. This custom setter
        accepts a correctly typed value, only, instead of an indeterminate
        string.

        Arguments:
            name: The name.
        """
        self.name_field = name

    @property
    def description(self) -> Description:
        """The description for this wish list. This computed property returns the
        correctly typed value instead of an indeterminate string.

        Returns:
            The description.
        """
        return Description(self.description_field)

    @description.setter
    def description(self, description: Description) -> None:
        """The setter for the description of this wish list. This custom setter
        accepts a correctly typed value, only, instead of an indeterminate
        string.

        Arguments:
            description: The description.
        """
        self.description_field = description

    @property
    def visibility(self) -> Visibility:
        """The visibility of this wish list. This computed property returns the
        correctly typed value instead of an indeterminate string.

        Returns:
            A value from the Visibility choices.
        """
        return Visibility(self.visibility_field)

    @visibility.setter
    def visibility(self, visibility: Visibility) -> None:
        """The setter for the visibility of this wish list. This custom setter
        accepts a correctly typed value, only, instead of an indeterminate
        string.

        Arguments:
            visibility: A value from the Visibility choices.
        """
        self.visibility_field = visibility

    @property
    def item_ordering(self) -> ItemOrdering:
        """The ordering of items for this wish list. This computed property
        returns the correctly typed value instead of an indeterminate string.

        Returns:
            A value from the ItemOrdering choices.
        """
        return ItemOrdering(self.item_ordering_field)

    @item_ordering.setter
    def item_ordering(self, item_ordering: ItemOrdering) -> None:
        """The setter for the ordering of items for this wish list. This custom
        setter accepts a correctly typed value, only, instead of an
        indeterminate string.

        Arguments:
            item_ordering:  A value from the ItemOrdering choices.
        """
        self.item_ordering_field = item_ordering
