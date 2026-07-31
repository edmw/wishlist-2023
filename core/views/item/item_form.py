import logging
from typing import Any

from django.forms import ModelForm, Select, Textarea, TextInput
from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseBase
from django.utils.translation import gettext as _
from django.utils.translation import gettext_noop

from core.models import Wish
from core.views._base import CreateView, LoginRequiredMixin, UpdateView, WishModelMixin
from core.views._forms import (
    AriaDescribedByMixin,
    LabelBeforeMixin,
    PlaceholderTextMixin,
    SelectStylesMixin,
    TextareaStylesMixin,
    TextStylesMixin,
)

from ._base import HasPermissionForItemViewMixin

logger = logging.getLogger(__name__)


class NameWidget(
    LabelBeforeMixin,
    PlaceholderTextMixin,
    AriaDescribedByMixin,
    TextStylesMixin,
    TextInput,
):
    label_text = gettext_noop("Name")
    placeholder_text = gettext_noop("Enter wish’s name")


class DescriptionWidget(
    LabelBeforeMixin,
    PlaceholderTextMixin,
    AriaDescribedByMixin,
    TextareaStylesMixin,
    Textarea,
):
    label_text = gettext_noop("Description")
    placeholder_text = gettext_noop("Enter wish’s description")


class PreferenceWidget(  # pyright: ignore[reportIncompatibleMethodOverride]
    LabelBeforeMixin,
    AriaDescribedByMixin,
    SelectStylesMixin,
    Select,
):
    label_text = gettext_noop("Preference")


class ReferenceWidget(
    LabelBeforeMixin,
    PlaceholderTextMixin,
    AriaDescribedByMixin,
    TextStylesMixin,
    TextInput,
):
    label_text = gettext_noop("URL")
    placeholder_text = gettext_noop("Enter URL (optional)")


class ReferencePhotoWidget(
    LabelBeforeMixin,
    PlaceholderTextMixin,
    AriaDescribedByMixin,
    TextStylesMixin,
    TextInput,
):
    label_text = gettext_noop("Photo URL")
    placeholder_text = gettext_noop("Enter photo URL (optional)")


class ItemForm(ModelForm):
    class Meta:
        model = Wish
        fields = [
            Wish.Fields.NAME,
            Wish.Fields.DESCRIPTION,
            Wish.Fields.PREFERENCE,
            Wish.Fields.REFERENCE,
            Wish.Fields.REFERENCE_PHOTO,
        ]
        widgets = {
            Wish.Fields.NAME: NameWidget,
            Wish.Fields.DESCRIPTION: DescriptionWidget,
            Wish.Fields.PREFERENCE: PreferenceWidget,
            Wish.Fields.REFERENCE: ReferenceWidget,
            Wish.Fields.REFERENCE_PHOTO: ReferencePhotoWidget,
        }


class ItemCreateView(
    LoginRequiredMixin,
    HasPermissionForItemViewMixin,
    WishModelMixin,
    CreateView,
):
    http_method_names = ["get", "post", "head", "options"]

    page_title = gettext_noop("Add a Wish")
    form_class = ItemForm
    form_title = gettext_noop("Add Wish")
    template_name = "item/item_form.html"

    success_url = "/"
    success_message = gettext_noop("Your new wish has been successfully added.")
    error_message_too_many_wishes = gettext_noop(
        "You already have too many wishes on this wish list. "
        "Please delete some wishes before you add new ones."
    )

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseBase:
        if wishlist := self.try_wishlist():
            if wishlist.wishes_count >= Wish.MAXIMUM_NUMBER_OF_WISHES_PER_WISHLIST:
                return self.redirect_back_with_error_message(_(self.error_message_too_many_wishes))

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: ModelForm) -> HttpResponse:
        form.instance.wishlist = self.try_wishlist()
        return super().form_valid(form)


class ItemUpdateView(
    LoginRequiredMixin,
    HasPermissionForItemViewMixin,
    WishModelMixin,
    UpdateView,
):
    http_method_names = ["get", "post", "head", "options"]

    page_title = gettext_noop("Update your Wish")
    form_class = ItemForm
    form_title = gettext_noop("Update Wish")
    template_name = "item/item_form.html"

    success_url = "/"
    success_message = gettext_noop("Your updated wish has been successfully saved.")
