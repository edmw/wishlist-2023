import logging

from django.core.exceptions import BadRequest
from django.db.models import QuerySet
from django.utils.translation import gettext_noop

from core.models import Reservation, Wish
from core.views._base import DeleteView, LoginRequiredMixin, WishMixin

from ._base import HasPermissionForItemViewMixin

logger = logging.getLogger(__name__)


class ItemReleaseView(
    LoginRequiredMixin,
    HasPermissionForItemViewMixin,
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

    def get_object(self, queryset: QuerySet[Wish] | None = None) -> Reservation:
        wish = self.assert_permission_for_wish(self.try_wish())
        if not wish.is_reserved:
            raise BadRequest()
        return wish.reservation
