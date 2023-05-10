from typing import Any, Iterable, Protocol, cast

from core.models._typing import HasModelState, HasPrimaryKey, IsSaveable


class ModelSupportsSave(HasPrimaryKey, HasModelState, Protocol):
    pass


class OnSaveNotifyMixin(IsSaveable):
    def save(
        self: ModelSupportsSave,
        force_insert: bool = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
        **kwargs: Any,
    ) -> None:
        from . import Wish

        notify_enabled = kwargs.pop("notify", True)

        created = self._state.adding
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
            **kwargs,
        )

        wish = cast(Wish, self)
        if created and notify_enabled:
            from core.tasks.wish import notify_on_create

            notify_on_create.apply_async(
                kwargs={
                    "wish_id": wish.id,
                },
            )  # type:ignore
