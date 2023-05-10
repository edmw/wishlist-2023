import logging
from typing import cast

from django.core.exceptions import BadRequest
from django.db.models import QuerySet
from django.utils.translation import gettext_noop

from core.models import Reservation
from core.views._base import DeleteView, LoginRequiredMixin, ReservationModelMixin

from ._base import HasPermissionForReservationViewMixin

logger = logging.getLogger(__name__)


class ReservationUndoView(
    LoginRequiredMixin,
    HasPermissionForReservationViewMixin,
    ReservationModelMixin,
    DeleteView,
):
    http_method_names = ["get", "post", "head", "options"]

    page_title = gettext_noop("Undo a Reservation")
    form_title = gettext_noop("Undo Reservation")
    template_name = "reservation/reservation_undo.html"

    success_url = "/"
    success_message = gettext_noop("The reservation for the wish has been successfully undone.")

    def get_object(self, queryset: QuerySet[Reservation] | None = None) -> Reservation:
        reservation = cast(Reservation, super().get_object(queryset))
        if not reservation.undoable:
            raise BadRequest()
        return reservation
