import logging
from typing import Any, cast

from django.db.utils import IntegrityError
from django.forms import ModelForm
from django.http import HttpResponse
from django.utils.translation import gettext as _
from django.utils.translation import gettext_noop

from core import constants
from core.models import Reservation, WishID
from core.services import WishService
from core.views._base import CreateView, LoginRequiredMixin, ReservationModelMixin
from webapp.services import LoggingService

from ._base import HasPermissionForReservationViewToCreateMixin

logger = logging.getLogger(__name__)


class ReservationCreateView(
    LoginRequiredMixin,
    HasPermissionForReservationViewToCreateMixin,
    ReservationModelMixin,
    CreateView,
):
    http_method_names = ["get", "post", "head", "options"]

    page_title = gettext_noop("Reserve a Wish")
    form_title = gettext_noop("Reserve Wish")
    fields = [Reservation.Fields.WISH]
    template_name = "reservation/reservation_create.html"

    success_url = "/"
    success_message = gettext_noop("The wish has been successfully reserved for you.")
    error_message_reservation_exists = gettext_noop("This wish has already been reserved.")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        wish_id = WishID(self.request.GET[constants.ITEM_ID_KEY])
        wish = WishService.get_wish(id=wish_id)
        context["wish"] = wish

        return context

    def form_valid(self, form: ModelForm) -> HttpResponse:
        reservation = cast(Reservation, form.instance)
        reservation.holder = self.try_user()
        try:
            return super().form_valid(form)
        except IntegrityError:
            LoggingService.suspicious_request(
                "Reservation exists for %r and %r",
                reservation.holder,
                reservation.wish,
                logger=logger,
                request=self.request,
            )
            return self.redirect_back_with_warning_message(_(self.error_message_reservation_exists))
