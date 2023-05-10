import logging

from django.forms import CheckboxInput, ModelForm
from django.utils.translation import gettext_noop

from core.models.favorite import Favorite
from core.views._base import FavoriteModelMixin, LoginRequiredMixin, UpdateView
from core.views._forms import CheckboxStylesMixin, LabelAfterMixin

from ._base import HasPermissionForFavoriteViewMixin

logger = logging.getLogger(__name__)


class NotifyOnItemCreateWidget(
    LabelAfterMixin,
    CheckboxStylesMixin,
    CheckboxInput,
):
    label_text = gettext_noop("Notify on wish create")


class FavoriteForm(ModelForm):
    class Meta:
        model = Favorite
        fields = [
            Favorite.Fields.NOTIFY_ON_ITEM_CREATE,
        ]
        widgets = {
            Favorite.Fields.NOTIFY_ON_ITEM_CREATE: NotifyOnItemCreateWidget,
        }


class FavoriteUpdateView(
    LoginRequiredMixin,
    HasPermissionForFavoriteViewMixin,
    FavoriteModelMixin,
    UpdateView,
):
    http_method_names = ["get", "post", "head", "options"]

    page_title = gettext_noop("Update your Favorite")
    form_class = FavoriteForm
    form_title = gettext_noop("Update Favorite")
    template_name = "favorite/favorite_form.html"

    success_url = "/"
    success_message = gettext_noop("Your updated favorite has been successfully saved.")
