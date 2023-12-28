from __future__ import annotations

from typing import Generic, Type, TypeVar
from uuid import UUID

T = TypeVar("T", bound=UUID)


class IDMixin(Generic[T]):
    id_type: Type[T]

    @property
    def id(self) -> T:
        """The identifier for this entity. This computed property returns the
        correctly typed identifier instead of an indeterminate UUID.

        Returns:
            The identifier.
        """
        return self.id_type(bytes=self.id_field.bytes)

    @id.setter
    def id(self, id: T) -> None:
        """The setter for the identifier of this entity. This custom setter
        accepts a correctly typed identifier, only, instead of an indeterminate
        UUID.

        Arguments:
            id: The identifier.
        """
        self.id_field = id
