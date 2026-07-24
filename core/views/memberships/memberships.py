import logging
from typing import Any, cast

from django.db.models import QuerySet
from django.utils.translation import gettext_noop

from core.models import WishlistMembership
from core.services import WishlistCollaborationService
from core.views._base import ListView, LoginRequiredMixin, WishlistMixin

from ._base import HasPermissionForMembershipsViewMixin

logger = logging.getLogger(__name__)


class MembershipsView(
    LoginRequiredMixin,
    HasPermissionForMembershipsViewMixin,
    WishlistMixin,
    ListView,
):
    http_method_names = ["get", "head", "options"]

    model = WishlistMembership
    page_title = gettext_noop("Members")
    template_name = "memberships/memberships.html"
    context_object_name = "memberships"

    def get_queryset(self) -> QuerySet[WishlistMembership]:
        wishlist = self.try_wishlist()
        return WishlistCollaborationService.list_memberships(wishlist=wishlist)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        wishlist = self.try_wishlist()
        object_list = cast(QuerySet[WishlistMembership], self.object_list)
        memberships = list(object_list.all())

        context["wishlist"] = wishlist
        context["memberships"] = memberships
        context["memberships_count"] = len(memberships)

        return context
