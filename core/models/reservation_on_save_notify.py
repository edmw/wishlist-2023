from typing import Any, Iterable, Protocol, cast

from django.db.models.base import ModelBase

from core.models._typing import HasModelState, HasPrimaryKey, IsSaveable


class ModelSupportsSave(HasPrimaryKey, HasModelState, Protocol):
    pass


class OnSaveNotifyMixin(IsSaveable):
    def save(
        self: ModelSupportsSave,
        *args,
        force_insert: bool | tuple[ModelBase, ...] = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
        **kwargs: Any,
    ) -> None:
        from .reservation import Reservation

        notify_enabled = kwargs.pop("notify", True)

        created = self._state.adding
        super().save(
            *args,
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
            **kwargs,
        )

        reservation = cast(Reservation, self)
        if created and notify_enabled:
            from core.tasks.wish import notify_on_reservation_create

            notify_on_reservation_create.apply_async(
                kwargs={
                    "wish_id": reservation.wish_id,
                },
            )
