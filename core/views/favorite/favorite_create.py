import logging
from typing import Any, cast

from django.db.utils import IntegrityError
from django.forms import ModelForm
from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext as _
from django.utils.translation import gettext_noop

from core import constants
from core.models import Favorite, WishlistID
from core.services import FavoriteService, WishlistService
from core.views._base import CreateView, FavoriteModelMixin, LoginRequiredMixin
from webapp.services import LoggingService

from ._base import HasPermissionForFavoriteViewMixin

logger = logging.getLogger(__name__)


class FavoriteCreateView(
    LoginRequiredMixin,
    HasPermissionForFavoriteViewMixin,
    FavoriteModelMixin,
    CreateView,
):
    http_method_names = ["get", "post", "head", "options"]

    page_title = gettext_noop("Add a Favorite")
    form_title = gettext_noop("Add Favorite")
    fields = [Favorite.Fields.WISHLIST]
    template_name = "favorite/favorite_create.html"

    success_url = "/"
    success_message = gettext_noop("The wish list has been successfully added to your favorites.")
    error_message_too_many_favorites = gettext_noop(
        "You already have too many wish lists in your favorites. "
        "Please remove some favorites before adding new ones."
    )
    error_message_favorite_exists = gettext_noop("You already have this wish list in your favorites.")

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if user := self.user:
            favorites_count = FavoriteService.count_favorites_for_user(user=user)
            if favorites_count >= Favorite.MAXIMUM_NUMBER_OF_FAVORITES_PER_USER:
                return self.redirect_back_with_error_message(_(self.error_message_too_many_favorites))

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        wishlist_id = WishlistID(self.request.GET[constants.LIST_ID_KEY])
        wishlist = WishlistService.get_wishlist(id=wishlist_id)
        context["wishlist"] = wishlist
        return context

    def form_valid(self, form: ModelForm) -> HttpResponse:
        favorite = cast(Favorite, form.instance)
        favorite.user = self.try_user()
        try:
            return super().form_valid(form)
        except IntegrityError:
            LoggingService.suspicious_request(
                "Favorite exists for %r and %r",
                favorite.user,
                favorite.wishlist,
                logger=logger,
                request=self.request,
            )
            return self.redirect_back_with_warning_message(_(self.error_message_favorite_exists))
