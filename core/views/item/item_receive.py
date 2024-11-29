import logging
from typing import Any, cast

from django.core.exceptions import BadRequest, ValidationError
from django.db.models import QuerySet
from django.forms import ModelForm
from django.http import HttpRequest
from django.http.response import HttpResponseBase
from django.utils.translation import gettext as _
from django.utils.translation import gettext_noop

from core.models import Reservation
from core.services import ReservationNotCompletableError, ReservationService
from core.views._base import LoginRequiredMixin, UpdateView, WishMixin

from ..reservation._base import HasPermissionForReservationViewMixin

logger = logging.getLogger(__name__)


class ItemReceiveForm(ModelForm):
    class Meta:
        model = Reservation
        fields = [
            Reservation.Fields.COMPLETED,
        ]

    def __init__(self, *args: Any, **kwargs: Any):
        initial = kwargs.get("initial", {})
        initial[Reservation.Fields.COMPLETED] = True
        kwargs["initial"] = initial
        super().__init__(*args, **kwargs)

    def clean(self) -> dict[str, Any]:
        reservation = cast(Reservation, self.instance)
        try:
            ReservationService.complete(reservation=reservation, save=False)
        except ReservationNotCompletableError as rnce:
            raise ValidationError(_("This wish can not be received."), code="not_receivable") from rnce
        return super().clean()


class ItemReceiveView(
    LoginRequiredMixin,
    HasPermissionForReservationViewMixin,
    WishMixin,
    UpdateView,
):
    http_method_names = ["get", "post", "head", "options"]

    model = Reservation
    page_title = gettext_noop("Receive your Wish")
    form_class = ItemReceiveForm
    form_title = gettext_noop("Receive Wish")
    template_name = "item/item_receive.html"

    success_url = "/"
    success_message = gettext_noop("The wish has been successfully marked as received.")
    error_message_not_receivable = gettext_noop(
        "This wish can not be received. May be it is not reserved yet."
    )

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseBase:
        wish = self.try_wish()
        if not wish.receivable:
            return self.redirect_back_with_error_message(_(self.error_message_not_receivable))

        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset: QuerySet[Reservation] | None = None) -> Reservation:
        wish = self.try_wish()
        if not wish.receivable:
            raise BadRequest()
        return wish.reservation
