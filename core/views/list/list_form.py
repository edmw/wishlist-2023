import logging
from typing import Any

from django.forms import CheckboxInput, ModelForm, RadioSelect, Select, TextInput
from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext as _
from django.utils.translation import gettext_noop

from core.models import Wishlist
from core.services import WishlistService
from core.views._base import (
    CreateView,
    LoginRequiredMixin,
    UpdateView,
    WishlistModelMixin,
)
from core.views._forms import (
    AriaDescribedByMixin,
    CheckboxStylesMixin,
    LabelAfterMixin,
    LabelBeforeMixin,
    PlaceholderTextMixin,
    RadioSelectStylesMixin,
    SelectStylesMixin,
    TextStylesMixin,
)

from ._base import HasPermissionForListViewMixin

logger = logging.getLogger(__name__)


class NameWidget(
    LabelBeforeMixin,
    PlaceholderTextMixin,
    AriaDescribedByMixin,
    TextStylesMixin,
    TextInput,
):
    label_text = gettext_noop("Name")
    placeholder_text = gettext_noop("Enter wish list’s name")

    def __init__(self) -> None:
        super().__init__()


class VisibilityWidget(
    LabelBeforeMixin,
    AriaDescribedByMixin,
    RadioSelectStylesMixin,
    RadioSelect,
):
    label_text = gettext_noop("Visibility")


class ItemOrderingWidget(
    LabelBeforeMixin,
    AriaDescribedByMixin,
    SelectStylesMixin,
    Select,
):
    label_text = gettext_noop("Display order of wishes")


class MarkReservationsWidget(
    LabelAfterMixin,
    CheckboxStylesMixin,
    CheckboxInput,
):
    label_text = gettext_noop("Don't spoil my surprises")


class ListForm(ModelForm):
    class Meta:
        model = Wishlist
        fields = [
            Wishlist.Fields.NAME,
            Wishlist.Fields.VISIBILITY,
            Wishlist.Fields.ITEM_ORDERING,
            Wishlist.Fields.MASK_RESERVATIONS,
        ]
        widgets = {
            Wishlist.Fields.NAME: NameWidget,
            Wishlist.Fields.VISIBILITY: VisibilityWidget,
            Wishlist.Fields.ITEM_ORDERING: ItemOrderingWidget,
            Wishlist.Fields.MASK_RESERVATIONS: MarkReservationsWidget,
        }


class ListCreateView(
    LoginRequiredMixin,
    HasPermissionForListViewMixin,
    WishlistModelMixin,
    CreateView,
):
    http_method_names = ["get", "post", "head", "options"]

    page_title = gettext_noop("Create new Wish List")
    form_class = ListForm
    form_title = gettext_noop("Create Wish List")
    template_name = "list/list_form.html"

    success_url = "/"
    success_message = gettext_noop("Your new wish list has been successfully created.")
    error_message_too_many_lists = gettext_noop(
        "You already have too many wish lists. Please delete some wish lists before you create new ones."
    )

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if user := self.user:
            wishlists_count = WishlistService.count_wishlists_for_user(user=user)
            if wishlists_count >= Wishlist.MAXIMUM_NUMBER_OF_WISHLISTS_PER_USER:
                return self.redirect_back_with_error_message(_(self.error_message_too_many_lists))

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: ModelForm) -> HttpResponse:
        form.instance.owner = self.try_user()
        return super().form_valid(form)


class ListUpdateView(
    LoginRequiredMixin,
    HasPermissionForListViewMixin,
    WishlistModelMixin,
    UpdateView,
):
    http_method_names = ["get", "post", "head", "options"]

    page_title = gettext_noop("Update your Wish List")
    form_class = ListForm
    form_title = gettext_noop("Update Wish List")
    template_name = "list/list_form.html"

    success_url = "/"
    success_message = gettext_noop("Your updated wish list has been successfully saved.")
