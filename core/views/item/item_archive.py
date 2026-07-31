import logging
from typing import Any, cast

from django.core.exceptions import BadRequest, ValidationError
from django.db.models import QuerySet
from django.forms import ModelForm
from django.utils.translation import gettext as _
from django.utils.translation import gettext_noop

from core.models import Wish
from core.services import WishNotArchivableError, WishService
from core.views._base import LoginRequiredMixin, UpdateView, WishModelMixin

from ._base import HasPermissionForItemViewMixin

logger = logging.getLogger(__name__)


class ItemArchiveForm(ModelForm):
    class Meta:
        model = Wish
        fields = [
            Wish.Fields.ARCHIVED,
        ]

    def __init__(self, *args: Any, **kwargs: Any):
        initial = kwargs.get("initial", {})
        initial[Wish.Fields.ARCHIVED] = True
        kwargs["initial"] = initial
        super().__init__(*args, **kwargs)

    def clean(self) -> dict[str, Any] | None:
        wish = cast(Wish, self.instance)
        try:
            WishService.archive(wish=wish, save=False)
        except WishNotArchivableError as wnae:
            raise ValidationError(_("This wish can not be archived."), code="not_archivable") from wnae
        return super().clean()


class ItemArchiveView(
    LoginRequiredMixin,
    HasPermissionForItemViewMixin,
    WishModelMixin,
    UpdateView,
):
    http_method_names = ["get", "post", "head", "options"]

    page_title = gettext_noop("Archive your Wish")
    form_class = ItemArchiveForm
    form_title = gettext_noop("Archive Wish")
    template_name = "item/item_archive.html"

    success_url = "/"
    success_message = gettext_noop("Your wish has been successfully archived.")

    def get_object(self, queryset: QuerySet[Wish] | None = None) -> Wish:
        wish = cast(Wish, super().get_object())
        if not wish.archivable:
            raise BadRequest()
        return wish
