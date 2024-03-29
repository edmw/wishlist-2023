import logging
from typing import Any

from django.forms import ModelForm
from django.utils.translation import gettext_noop

from core.models import Wish
from core.views._base import DetailView, LoginRequiredMixin, WishModelMixin

from ._base import HasPermissionForItemViewMixin
from .item_archive import ItemArchiveForm
from .item_move import ItemMoveForm
from .item_unarchive import ItemUnarchiveForm

logger = logging.getLogger(__name__)


class ItemManageForm(ModelForm):
    class Meta:
        model = Wish
        fields = [
            Wish.Fields.NAME,
        ]
        widgets = {}


class ItemManageView(
    LoginRequiredMixin,
    HasPermissionForItemViewMixin,
    WishModelMixin,
    DetailView,
):
    http_method_names = ["get", "head", "options"]

    page_title = gettext_noop("Manage your Wish")
    template_name = "item/item_manage.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        user = self.try_user()
        item = self.get_object()
        context["move_form"] = ItemMoveForm(user=user, instance=item)
        context["archive_form"] = ItemArchiveForm(instance=item)
        context["unarchive_form"] = ItemUnarchiveForm(instance=item)

        return context
