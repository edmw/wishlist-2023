from typing import Any, cast

from core.models._typing import HasPrimaryKey, IsDeletable


class OnDeleteNotifyMixin(IsDeletable):
    def delete(self: HasPrimaryKey, *args: Any, **kwargs: Any) -> Any:
        from .reservation import Reservation

        super().delete(*args, **kwargs)

        reservation = cast(Reservation, self)
        from core.tasks.wish import notify_on_reservation_delete

        notify_on_reservation_delete.apply_async(
            kwargs={
                "wish_id": reservation.wish_id,
            },
        )
