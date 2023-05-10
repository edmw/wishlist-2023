"""Base views."""

from typing import Any, cast

import django.contrib.auth.mixins
import django.db.models
import django.views.generic
import django.views.generic.base
import django.views.generic.edit
from django.contrib import messages
from django.core.exceptions import BadRequest
from django.forms import ModelForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.utils.translation import gettext as _

from core import constants
from core.models import Favorite, Reservation, User, Wish, WishID, Wishlist, WishlistID
from core.services import (
    FavoriteService,
    ReservationService,
    URLService,
    WishlistService,
    WishService,
)
from webapp.services import LanguageService
from webapp.views import AddNeverCacheMixin

from ._typing import SupportsViewSetup


class UserMixin(SupportsViewSetup):
    user: User | None

    def try_user(self) -> User:
        """Returns the authenticated user. If there is no authenticated user
        raises a `BadRequest` exception."""
        if not self.user:
            raise BadRequest("Authenticated user required.")
        return self.user

    def setup(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
        super().setup(request, *args, **kwargs)
        user = request.user
        self.user = cast(User, user) if user.is_authenticated else None


class WishlistModelMixin(UserMixin):
    model = Wishlist
    pk_url_kwarg = constants.LIST_ID_KEY

    def get_queryset(self) -> django.db.models.QuerySet[Wishlist]:
        user = self.try_user()
        return WishlistService.query_wishlists_for_user(user=user)


class WishlistMixin(SupportsViewSetup):
    wishlist_id: WishlistID | None = None
    wishlist: Wishlist | None = None

    def try_wishlist(self) -> Wishlist:
        """Returns the requested wishlist. If there is no wishlist
        raises a `BadRequest` exception."""
        if not self.wishlist_id:
            raise BadRequest("List ID required.")

        if not self.wishlist or self.wishlist.id != self.wishlist_id:
            wishlist = WishlistService.get_wishlist(id=self.wishlist_id)
            self.wishlist = wishlist

        if not self.wishlist:
            raise BadRequest("List required.")

        return self.wishlist

    def setup(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
        super().setup(request, *args, **kwargs)
        self.wishlist_id = kwargs.get(constants.LIST_ID_KEY)


class WishModelMixin(WishlistMixin):
    model = Wish
    pk_url_kwarg = constants.ITEM_ID_KEY

    def get_queryset(self) -> django.db.models.QuerySet[Wish]:
        wishlist = self.try_wishlist()
        return WishService.query_wishes_for_wishlist(wishlist=wishlist)


class WishMixin(SupportsViewSetup):
    wish_id: WishID | None = None
    wish: Wish | None = None

    def try_wish(self) -> Wish:
        """Returns the requested wish. If there is no wish
        raises a `BadRequest` exception.
        """
        if not self.wish_id:
            raise BadRequest("Wish ID required.")

        if not self.wish or self.wish.id != self.wish_id:
            wish = WishService.get_wish(id=self.wish_id)
            self.wish = wish

        if not self.wish:
            raise BadRequest("Wish required.")

        return self.wish

    def setup(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
        super().setup(request, *args, **kwargs)
        self.wish_id = kwargs.get(constants.ITEM_ID_KEY)


class FavoriteModelMixin(UserMixin):
    model = Favorite
    pk_url_kwarg = constants.FAVORITE_ID_KEY

    def get_queryset(self) -> django.db.models.QuerySet[Favorite]:
        user = self.try_user()
        return FavoriteService.query_favorites_for_user(user=user)


class ReservationModelMixin(UserMixin):
    model = Reservation
    pk_url_kwarg = constants.RESERVATION_ID_KEY

    def get_queryset(self) -> django.db.models.QuerySet[Reservation]:
        user = self.try_user()
        return ReservationService.query_reservations_for_user(user=user)


class LoginRequiredMixin(django.contrib.auth.mixins.LoginRequiredMixin, UserMixin):
    """A mixin that requires a login and provides a user attribute for the
    authenticated user.
    """


class PageContextMixin(django.views.generic.base.ContextMixin):
    """A page view mixin that populates the render context with page-related
    values.
    """

    page_title: str | None = None

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        return context


class FormContextMixin(django.views.generic.FormView):
    """A form view mixin that populates the render context with form-related
    values.
    """

    form_title: str | None = None

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = self.form_title
        return context


class FormSuccessMessageMixin(django.views.generic.FormView):
    """A form view mixin that emits a message specified in the form view after
    it completes successfully.
    """

    success_message: str

    def form_valid(self, form: ModelForm) -> HttpResponse:
        result = super().form_valid(form)
        if message := getattr(self, "success_message", None):
            messages.success(self.request, _(message))
        return result


class FormSuccessRedirectMixin(django.views.generic.FormView):
    """A form view mixin that redirects to a url specified in the query after
    it completes successfully.
    """

    def get_success_url(self) -> str:
        """Returns the success url which is the url given in the query
        parameter named "p". If no query parameter is given, returns the
        default url.
        """
        if url := self.request.GET.get("p"):
            if URLService.url_is_absolute_path(url=url):
                return url
        return super().get_success_url()


class FormBackRedirectMixin(django.views.generic.FormView):
    """A form view mixin that redirects to a url specified in the query to
    go back.
    """

    def get_back_url(self) -> str:
        """Returns the back url which is the url given in the query
        parameter named "p". If no query parameter is given, returns "/".
        """
        if url := self.request.GET.get("p"):
            if URLService.url_is_absolute_path(url=url):
                return url
        return "/"

    def redirect_back_with_warning_message(self, message: str) -> HttpResponse:
        messages.warning(self.request, message)
        return redirect(self.get_back_url())

    def redirect_back_with_error_message(self, message: str) -> HttpResponse:
        messages.error(self.request, message)
        return redirect(self.get_back_url())


class DetailView(
    AddNeverCacheMixin,
    PageContextMixin,
    django.views.generic.DetailView,
):
    """The base view to show model data."""


class ListView(
    AddNeverCacheMixin,
    PageContextMixin,
    django.views.generic.ListView,
):
    """The base view to list model data."""


class FormView(
    AddNeverCacheMixin,
    PageContextMixin,
    FormContextMixin,
    FormSuccessMessageMixin,
    FormSuccessRedirectMixin,
    FormBackRedirectMixin,
    django.views.generic.edit.FormView,
):
    """The base view for generic form views."""


class CreateView(
    AddNeverCacheMixin,
    PageContextMixin,
    FormContextMixin,
    FormSuccessMessageMixin,
    FormSuccessRedirectMixin,
    FormBackRedirectMixin,
    django.views.generic.edit.CreateView,
):
    """The base view to create model data."""


class UpdateView(
    AddNeverCacheMixin,
    PageContextMixin,
    FormContextMixin,
    FormSuccessMessageMixin,
    FormSuccessRedirectMixin,
    FormBackRedirectMixin,
    django.views.generic.edit.UpdateView,
):
    """The base view to edit model data."""


class DeleteView(
    AddNeverCacheMixin,
    PageContextMixin,
    FormContextMixin,
    FormSuccessMessageMixin,
    FormSuccessRedirectMixin,
    FormBackRedirectMixin,
    django.views.generic.edit.DeleteView,
):
    """The base view to delete model data."""


class TemplateView(PageContextMixin, django.views.generic.TemplateView):
    """A template view."""


class LocalizedTemplateView(PageContextMixin, django.views.generic.TemplateView):
    """A template view that adjusts the template to be loaded according to the
    active language.

    Inserts the language code between the template’s base name and the name’s
    "html" extension.

    For example
        "welcome.html"
    becomes
        "welcome.en.html"
    if the active language is english.

    NOTE: Does not support falling back to a generic template. So, there needs
    to exist a template for every supported language.
    """

    def get_template_names(self) -> list[str]:
        """Returns the configured template name, after modifying it to include
        the code of the activated language."""
        if language_code := LanguageService.get_language_code():
            return [self.template_name.replace(".html", f".{language_code}.html")]
        return [self.template_name]
