from typing import Any, Protocol

from django.db.models.base import ModelState


class HasPrimaryKey(Protocol):
    pk: Any | None


class HasModelState(Protocol):
    _state: ModelState


class IsSaveable:
    class SaveCallable(Protocol):
        def __call__(self, *args: Any, **kwargs: Any) -> None:
            ...

    save: SaveCallable


class IsDeletable:
    class DeleteCallable(Protocol):
        def __call__(self, *args: Any, **kwargs: Any) -> Any:
            ...

    delete: DeleteCallable
