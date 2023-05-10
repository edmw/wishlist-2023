import logging

from django.utils.translation import gettext_noop

from core.views._base import DeleteView, FavoriteModelMixin, LoginRequiredMixin

from ._base import HasPermissionForFavoriteViewMixin

logger = logging.getLogger(__name__)


class FavoriteDeleteView(
    LoginRequiredMixin,
    HasPermissionForFavoriteViewMixin,
    FavoriteModelMixin,
    DeleteView,
):
    http_method_names = ["get", "post", "head", "options"]

    page_title = gettext_noop("Remove a Favorite")
    form_title = gettext_noop("Remove Favorite")
    template_name = "favorite/favorite_delete.html"

    success_url = "/"
    success_message = gettext_noop("The wish list has been successfully removed from your favorites.")
