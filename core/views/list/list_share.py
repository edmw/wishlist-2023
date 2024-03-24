import logging
from typing import Any

from django.db.models import QuerySet
from django.forms import EmailField, EmailInput, Form
from django.utils.translation import gettext as _
from django.utils.translation import gettext_noop

from core.models import Wishlist, WishlistLens
from core.views._base import LoginRequiredMixin, UpdateView, WishlistModelMixin
from core.views._forms import (
    AriaDescribedByMixin,
    LabelBeforeMixin,
    PlaceholderTextMixin,
    TextStylesMixin,
)

from ._base import HasPermissionForListViewMixin

logger = logging.getLogger(__name__)


class ShareEmailWidget(
    LabelBeforeMixin,
    PlaceholderTextMixin,
    AriaDescribedByMixin,
    TextStylesMixin,
    EmailInput,
):
    placeholder_text = gettext_noop("Enter email")


class ShareEmailField(EmailField):
    widget = ShareEmailWidget


class ListShareForm(Form):
    email = ShareEmailField(required=True)

    def __init__(self, *args: Any, **kwargs: Any):
        self.instance = kwargs.pop("instance")
        super().__init__(*args, **kwargs)


class ListShareView(
    LoginRequiredMixin,
    HasPermissionForListViewMixin,
    WishlistModelMixin,
    UpdateView,
):
    http_method_names = ["get", "post", "head", "options"]

    page_title = gettext_noop("Share your List")
    form_title = gettext_noop("Share List")
    form_class = ListShareForm
    template_name = "list/list_share.html"

    success_url = "/"
    success_message = gettext_noop("An invitation for sharing your wish list has been successfully sent.")

    def get_queryset(self) -> QuerySet[Wishlist]:
        user = self.try_user()
        return WishlistLens.view().by_owner(user=user).queryset
