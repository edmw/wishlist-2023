import logging
from typing import Any, Protocol

from django.utils.translation import gettext_noop

from core.views._base import ListView, LoginRequiredMixin, WishModelMixin

from .._typing import HasObjectList, HasWishlist
from ._base import HasPermissionForItemsViewMixin

logger = logging.getLogger(__name__)


class IsItemsView(HasWishlist, HasObjectList, Protocol):
    ...


class ItemsView(
    LoginRequiredMixin,
    HasPermissionForItemsViewMixin,
    WishModelMixin,
    ListView,
):
    http_method_names = ["get", "post", "head", "options"]

    page_title = gettext_noop("Wishes")
    template_name = "items/items.html"

    def get_context_data(self: IsItemsView, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        wishlist = self.try_wishlist()
        context["wishlist"] = wishlist
        context["wishlist_size"] = wishlist.wishes_count

        wishes = []
        wishes_archived = []
        for wish in self.object_list.all():
            if wish.archived:
                wishes_archived.append(wish)
            else:
                wishes.append(wish)
        context["wishes"] = wishes
        context["wishes_count"] = len(wishes)
        context["wishes_archived"] = wishes_archived
        context["wishes_archived_count"] = len(wishes_archived)

        return context
