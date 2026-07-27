import logging

from django.core.exceptions import BadRequest
from django.db.models import QuerySet
from django.utils.translation import gettext_noop

from core.models import Reservation, Wish
from core.views._base import DeleteView, LoginRequiredMixin, WishMixin

from ._base import PermittedForItemViewMixin

logger = logging.getLogger(__name__)


class ItemReleaseView(
    LoginRequiredMixin,
    PermittedForItemViewMixin,
    WishMixin,
    DeleteView,
):
    http_method_names = ["get", "post", "head", "options"]

    model = Reservation
    page_title = gettext_noop("Delete a Reservation")
    form_title = gettext_noop("Delete Reservation")
    template_name = "item/item_release.html"

    success_url = "/"
    success_message = gettext_noop("The reservation for the wish has been successfully deleted.")

    def get_item(self, queryset: QuerySet[Wish] | None = None) -> Wish:
        return self.try_wish()

    def get_object(self, queryset: QuerySet[Reservation] | None = None) -> Reservation:
        wish = self.get_permitted_item()
        if not wish.is_reserved:
            raise BadRequest()
        return wish.reservation
