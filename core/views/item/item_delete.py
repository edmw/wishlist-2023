import logging
from typing import cast

from django.core.exceptions import BadRequest
from django.db.models import QuerySet
from django.utils.translation import gettext_noop

from core.models import Wish
from core.views._base import DeleteView, LoginRequiredMixin, WishModelMixin

from ._base import HasPermissionForItemViewMixin

logger = logging.getLogger(__name__)


class ItemDeleteView(
    LoginRequiredMixin,
    HasPermissionForItemViewMixin,
    WishModelMixin,
    DeleteView,
):
    http_method_names = ["get", "post", "head", "options"]

    page_title = gettext_noop("Delete a Wish")
    form_title = gettext_noop("Delete Wish")
    template_name = "item/item_delete.html"

    success_url = "/"
    success_message = gettext_noop("Your wish has been successfully deleted.")

    def get_object(self, queryset: QuerySet[Wish] | None = None) -> Wish:
        wish = cast(Wish, super().get_object(queryset))
        if not wish.deletable:
            raise BadRequest()
        return wish
