from __future__ import annotations

from typing import Any, Generic, Self, Type, TypeVar, cast

from django.db.models import Model, QuerySet

M = TypeVar("M", bound=Model)


class LensBase(Generic[M], object):
    model: Type[M]
    queryset: QuerySet[M]

    class Error(Exception):
        pass

    class StateError(Error):
        pass

    class LensAlreadyConsumedError(StateError):
        pass

    def __init__(self) -> None:
        """Initialises the lens with a view on all objects."""
        self.queryset = self.model.objects.all()
        self._is_consumed = False

    @classmethod
    def view(cls) -> Self:
        return cls()

    def _assert_not_consumed(self) -> None:
        if self._is_consumed:
            raise LensBase.LensAlreadyConsumedError

    def _consume(self) -> None:
        self._is_consumed = True

    def qs(self) -> QuerySet[M]:
        self._assert_not_consumed()
        return self.queryset.all()

    def count(self) -> int:
        self._assert_not_consumed()
        try:
            return self.queryset.count()
        finally:
            self._consume()

    def exists(self) -> bool:
        self._assert_not_consumed()
        try:
            return self.queryset.exists()
        finally:
            self._consume()

    def one(self) -> M:
        self._assert_not_consumed()
        try:
            return self.queryset.get()
        finally:
            self._consume()

    def first_or_none(self) -> M | None:
        self._assert_not_consumed()
        try:
            return self.queryset.first()
        finally:
            self._consume()

    def ids(self) -> list[int]:
        self._assert_not_consumed()
        try:
            return cast(list[int], list(self.queryset.values_list("pk", flat=True)))
        finally:
            self._consume()


class LensHasIdMixin:
    filter_for_id: Any | None = None

    class ViewAlreadyNarrowedDownToIDError(LensBase.StateError):
        pass

    def by_id(self, *, id: Any) -> Self:
        cast(LensBase[Any], self)._assert_not_consumed()
        match self.filter_for_id:
            case None:
                self.filter_for_id = id
                self.queryset = self.queryset.filter(id_field=id)
                return self
            case _ if self.filter_for_id == id:
                return self
            case _:
                raise LensHasIdMixin.ViewAlreadyNarrowedDownToIDError


class LensHasOrderMixin:
    order_by: str | None = None

    class ViewAlreadyOrderedError(LensBase.StateError):
        pass

    def ordered_by(self, field: str) -> Self:
        cast(LensBase[Any], self)._assert_not_consumed()
        match self.order_by:
            case None:
                self.order_by = field
                self.queryset = self.queryset.order_by(field)
                return self
            case _ if self.order_by == field:
                return self
            case _:
                raise LensHasOrderMixin.ViewAlreadyOrderedError
