from datetime import datetime

from core.models import Reservation, User, Wish, types


class ReservationFactory:
    @staticmethod
    def create(
        id: types.FavoriteID,
        holder: User,
        wish: Wish,
        completed: bool,
        completed_at: datetime | None,
    ) -> Reservation:
        """Create a reservation model instance without persisting it.

        Arguments:
            id: The identifier for the new reservation.
            holder: Holder of the new reservation.
            wish: Wish of the new reservation.
            completed: Completion of the new reservation.

        Returns:
            Reservation instance created.
        """
        return Reservation(
            id_field=id,
            holder=holder,
            wish=wish,
            completed=completed,
            completed_at=completed_at,
        )
