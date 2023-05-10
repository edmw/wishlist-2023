import logging
from typing import Any

from django.utils.translation import gettext_noop

from core.services import WishlistService
from core.views._base import ListView, LoginRequiredMixin, WishlistModelMixin

from ._base import HasPermissionForListsViewMixin

logger = logging.getLogger(__name__)


class ListsView(
    LoginRequiredMixin,
    HasPermissionForListsViewMixin,
    WishlistModelMixin,
    ListView,
):
    http_method_names = ["get", "head", "options"]

    page_title = gettext_noop("Wishlists")
    template_name = "lists/lists.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = {}

        user = self.try_user()
        context["your_wishlists_count"] = WishlistService.count_wishlists_for_user(user=user)
        context["your_wishlists"] = WishlistService.query_wishlists_for_user(user=user)

        return context
