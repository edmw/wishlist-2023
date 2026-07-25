import logging

from django.db.models import QuerySet
from django.utils.translation import gettext_noop

from core import constants
from core.models import WishlistMembership, WishlistMembershipLens
from core.views._base import DeleteView, LoginRequiredMixin, WishlistMixin
from core.views.memberships._base import HasPermissionForMembershipsViewMixin

logger = logging.getLogger(__name__)


class MembershipDeleteView(
    LoginRequiredMixin,
    HasPermissionForMembershipsViewMixin,
    WishlistMixin,
    DeleteView,
):
    http_method_names = ["get", "post", "head", "options"]

    model = WishlistMembership
    pk_url_kwarg = constants.MEMBERSHIP_ID_KEY

    page_title = gettext_noop("Remove a Contributor")
    form_title = gettext_noop("Remove Contributor")
    template_name = "membership/membership_delete.html"

    success_message = gettext_noop("The contributor has been successfully removed.")

    def get_queryset(self) -> QuerySet[WishlistMembership]:
        wishlist = self.try_wishlist()
        return WishlistMembershipLens.view().by_wishlist(wishlist=wishlist).for_listing().queryset.all()

    def get_success_url(self) -> str:
        return self.try_wishlist().get_absolute_memberships_url()
