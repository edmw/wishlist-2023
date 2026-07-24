"""All about viewing a user’s wishlists."""

import logging
from typing import Any

from core.models import FavoriteLens, WishlistLens
from core.services import FavoriteService, WishlistService
from core.views._base import TemplateView, UserMixin
from webapp.views import AddNeverCacheMixin

logger = logging.getLogger(__name__)


class StartView(UserMixin, AddNeverCacheMixin, TemplateView):
    """The view for a user’s wish list."""

    http_method_names = ["get", "head", "options"]

    template_name = "start/start.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        if user := self.user:
            context["your_wishlists_count"] = WishlistService.count_wishlists_for_user(user=self.user)
            context["your_wishlists"] = (
                WishlistLens.view().editable_by(user=self.user).for_listing().queryset.all()
            )
            context["your_wishlists_with_members"] = set(
                WishlistLens.view().by_owner(user=user).with_memberships().ids()
            )
            context["your_favorites_count"] = FavoriteService.count_favorites_for_user(user=self.user)
            context["your_favorites"] = FavoriteLens.view().by_user(user=user).for_listing().queryset.all()

        return context
