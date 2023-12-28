import logging
from typing import Any, cast

from django.core.exceptions import ValidationError
from django.forms import ModelChoiceField, ModelForm, Select
from django.utils.translation import gettext as _
from django.utils.translation import gettext_noop

from core.models import Wish
from core.models.wishlist.lens import WishlistLens
from core.views._base import LoginRequiredMixin, UpdateView, WishModelMixin
from core.views._forms import (
    AriaDescribedByMixin,
    LabelBeforeMixin,
    PlaceholderTextMixin,
    SelectStylesMixin,
)

from ._base import HasPermissionForItemViewMixin

logger = logging.getLogger(__name__)


class WishlistWidget(
    LabelBeforeMixin,
    PlaceholderTextMixin,
    AriaDescribedByMixin,
    SelectStylesMixin,
    Select,
):
    label_text = gettext_noop("Select a list to move your wish to")


class ItemMoveForm(ModelForm):
    def __init__(self, *args: Any, **kwargs: Any):
        user = kwargs.pop("user")
        instance = kwargs["instance"]
        wishlist_field = cast(ModelChoiceField, self.base_fields[Wish.Fields.WISHLIST])
        wishlist_field.queryset = (
            WishlistLens.view()
            .by_owner(user=user)
            .without_lists(lists=[instance.wishlist])
            .for_listing()
            .queryset.all()
        )
        wishlist_field.empty_label = None
        super().__init__(*args, **kwargs)

    class Meta:
        model = Wish
        fields = [
            Wish.Fields.WISHLIST,
        ]
        widgets = {
            Wish.Fields.WISHLIST: WishlistWidget,
        }

    def clean(self) -> dict[str, Any]:
        wish = cast(Wish, self.instance)
        if not wish.movable:
            raise ValidationError(_("This wish can not be moved."), code="not_movable")
        return super().clean()


class ItemMoveView(
    LoginRequiredMixin,
    HasPermissionForItemViewMixin,
    WishModelMixin,
    UpdateView,
):
    http_method_names = ["get", "post", "head", "options"]

    page_title = gettext_noop("Move your Wish")
    form_class = ItemMoveForm
    form_title = gettext_noop("Move Wish")
    template_name = "item/item_move.html"

    success_url = "/"
    success_message = gettext_noop("Your wish has been successfully moved.")

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.try_user()
        return kwargs
