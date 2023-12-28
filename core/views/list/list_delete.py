import logging
from typing import Any, cast

from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.forms import CharField, Form, TextInput
from django.utils.translation import gettext as _
from django.utils.translation import gettext_noop

from core.models import Name, Wishlist
from core.models.wishlist_lens import WishlistLens
from core.views._base import DeleteView, LoginRequiredMixin, WishlistModelMixin
from core.views._forms import (
    AriaDescribedByMixin,
    LabelBeforeMixin,
    PlaceholderTextMixin,
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
    placeholder_text = gettext_noop("Enter wish list’s name")


class NameField(CharField):
    widget = NameWidget


class ListDeleteForm(Form):
    name_confirmation = NameField(max_length=Name.max_length, required=False)

    WISHLIST_NAME_ARG = "wishlist_name"

    def __init__(self, *args: Any, **kwargs: Any):
        self.wishlist_name = kwargs.pop(self.WISHLIST_NAME_ARG)
        super().__init__(*args, **kwargs)

    def clean_name_confirmation(self) -> str:
        data = self.cleaned_data["name_confirmation"]
        if data == self.wishlist_name:
            return data

        raise ValidationError(
            _("The name entered does not match the name of the list to delete."),
            code="name_mismatch",
        )


class ListDeleteView(
    LoginRequiredMixin,
    HasPermissionForListViewMixin,
    WishlistModelMixin,
    DeleteView,
):
    http_method_names = ["get", "post", "head", "options"]

    page_title = gettext_noop("Delete your List")
    form_title = gettext_noop("Delete List")
    form_class = ListDeleteForm
    template_name = "list/list_delete.html"

    success_url = "/"
    success_message = gettext_noop("Your wish list has been successfully deleted.")

    def get_queryset(self) -> QuerySet[Wishlist]:
        user = self.try_user()
        return WishlistLens.view().by_owner(user=user).for_listing().queryset

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        wishlist = cast(Wishlist, self.get_object())
        if wishlist.wishes_count > 0:
            kwargs[ListDeleteForm.WISHLIST_NAME_ARG] = wishlist.name
        else:
            kwargs[ListDeleteForm.WISHLIST_NAME_ARG] = ""
        return kwargs
