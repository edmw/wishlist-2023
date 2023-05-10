import logging
from typing import Any, Protocol

import django.db.models
from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext_noop
from django.views.generic.detail import SingleObjectMixin

from core.models import Wish
from core.services import FavoriteService, PermissionService, WishService
from core.views._base import ListView, LoginRequiredMixin, WishlistMixin
from core.views._typing import (
    DoesViewDispatching,
    HasModel,
    HasObjectList,
    HasUser,
    HasWishlist,
)

logger = logging.getLogger(__name__)


class IsWishlistView(HasUser, HasWishlist, HasModel, HasObjectList, Protocol):
    ...


class HasPermissionForWishlistViewMixin(DoesViewDispatching, SingleObjectMixin):
    """Verifies the requesting user is allowed to access the wish list."""

    request: HttpRequest

    def dispatch(self: IsWishlistView, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Dispatches the request to the supported http method handler after
        verifying the requesting user is allowed to access the requested
        resource.

        A user has permission to perform the query if the list is owned by this
        user or the visibility setting of the list entitles this user.
        """
        wishlist = self.try_wishlist()
        PermissionService.assert_wishlist(
            requesting_user=self.try_user(),
            wishlist=wishlist,
        )

        return super().dispatch(request, *args, **kwargs)


class WishlistView(
    LoginRequiredMixin,
    HasPermissionForWishlistViewMixin,
    WishlistMixin,
    ListView,
):
    http_method_names = ["get", "head", "options"]

    model = Wish
    page_title = gettext_noop("Wishes")
    template_name = "wishlist/wishlist.html"

    def get_queryset(self) -> django.db.models.QuerySet[Wish]:
        wishlist = self.try_wishlist()
        return WishService.query_wishes_for_wishlist(
            wishlist=wishlist,
            archived=False,
        )

    def get_context_data(self: IsWishlistView, **kwargs: Any) -> dict[str, Any]:
        context = {}

        user = self.try_user()
        wishlist = self.try_wishlist()
        context["wishlist"] = wishlist
        context["wishlist_is_favorite"] = FavoriteService.is_favorite(wishlist=wishlist, user=user)
        wishes = self.object_list.all()
        context["wishes"] = wishes
        context["wishes_count"] = len(wishes)

        return context
