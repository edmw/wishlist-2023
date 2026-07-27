import logging
from typing import Any, cast

from django.http import HttpRequest, HttpResponse
from django.utils.text import slugify

from core.models import Wishlist
from core.services import SerializationService
from core.views._base import DetailView, LoginRequiredMixin, WishlistModelMixin

from ._base import HasPermissionForListViewMixin

logger = logging.getLogger(__name__)


class ListExportView(
    LoginRequiredMixin,
    HasPermissionForListViewMixin,
    WishlistModelMixin,
    DetailView,
):
    http_method_names = ["get", "head", "options"]

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        wishlist = cast(Wishlist, self.get_object())
        filename = f"{slugify(wishlist.name)}.yaml"
        yaml = SerializationService.wishlist_yaml(wishlist=wishlist)
        response = HttpResponse(content=yaml, content_type="application/yaml; charset=utf-8")
        response["Content-Disposition"] = f"attachment; filename={filename};"
        return response
