import logging
from typing import Any

from django.utils.translation import gettext_noop

from core.models import FavoriteLens
from core.services import FavoriteService
from core.views._base import FavoriteModelMixin, ListView, LoginRequiredMixin
from core.views.favorites._base import HasPermissionForFavoritesViewMixin

logger = logging.getLogger(__name__)


class FavoritesView(
    LoginRequiredMixin,
    HasPermissionForFavoritesViewMixin,
    FavoriteModelMixin,
    ListView,
):
    http_method_names = ["get", "head", "options"]

    page_title = gettext_noop("Favorites")
    template_name = "favorites/favorites.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        user = self.try_user()
        context["your_favorites_count"] = FavoriteService.count_favorites_for_user(user=user)
        context["your_favorites"] = FavoriteLens.view().by_user(user=user).for_listing().queryset.all()

        return context
