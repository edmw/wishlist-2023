from __future__ import annotations

from typing import Generic, Self, Type, TypeVar

from django.db.models import Model, QuerySet

M = TypeVar("M", bound=Model)


class LensBase(Generic[M], object):
    model: Type[M]
    queryset: QuerySet[M]

    class Error(Exception):
        pass

    class StateError(Error):
        pass

    def __init__(self) -> None:
        """Initialises the lens with a view on all objects."""
        self.queryset = self.model.objects

    @classmethod
    def view(cls) -> Self:
        return cls()


class LensHasOrderMixin:
    order_by: str | None = None

    class ViewAlreadyOrderedError(LensBase.StateError):
        pass

    def ordered_by(self, field: str) -> Self:
        match self.order_by:
            case None:
                self.order_by = field
                self.queryset = self.queryset.order_by(field)
                return self
            case _ if self.order_by == field:
                return self
            case _:
                raise LensHasOrderMixin.ViewAlreadyOrderedError
