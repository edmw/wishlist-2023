import logging
from typing import Any, cast

from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.utils.translation import gettext as _
from django.utils.translation import gettext_noop

from core.models import Wish
from core.services import WishNotUnarchivableError, WishService
from core.views._base import LoginRequiredMixin, UpdateView, WishModelMixin

from ._base import HasPermissionForItemViewMixin

logger = logging.getLogger(__name__)


class ItemUnarchiveForm(ModelForm):
    class Meta:
        model = Wish
        fields = [
            Wish.Fields.ARCHIVED,
        ]

    def __init__(self, *args: Any, **kwargs: Any):
        initial = kwargs.get("initial", {})
        initial[Wish.Fields.ARCHIVED] = False
        kwargs["initial"] = initial
        super().__init__(*args, **kwargs)

    def clean(self) -> dict[str, Any]:
        wish = cast(Wish, self.instance)
        try:
            WishService.unarchive(wish=wish, save=False)
        except WishNotUnarchivableError as wnue:
            raise ValidationError(_("This wish can not be unarchived."), code="not_unarchivable") from wnue
        return super().clean()


class ItemUnarchiveView(
    LoginRequiredMixin,
    HasPermissionForItemViewMixin,
    WishModelMixin,
    UpdateView,
):
    http_method_names = ["get", "post", "head", "options"]

    page_title = gettext_noop("Unarchive your Wish")
    form_class = ItemUnarchiveForm
    form_title = gettext_noop("Unarchive Wish")
    template_name = "item/item_unarchive.html"

    success_url = "/"
    success_message = gettext_noop("Your wish has been successfully unarchived.")
