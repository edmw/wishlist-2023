"""The Core’s views."""

from .favorite import FavoriteCreateView, FavoriteDeleteView, FavoriteUpdateView
from .favorites import FavoritesView
from .item import (
    ItemArchiveView,
    ItemCreateView,
    ItemDeleteView,
    ItemManageView,
    ItemMoveView,
    ItemReceiveView,
    ItemReleaseView,
    ItemUnarchiveView,
    ItemUpdateView,
)
from .items import ItemsView
from .legal_notice import LegalNoticeView
from .list import ListCreateView, ListDeleteView, ListExportView, ListUpdateView
from .lists import ListsView
from .memberships import MembershipsView
from .privacy_policy import PrivacyPolicyView
from .reservation import ReservationCreateView, ReservationUndoView
from .start import StartView
from .user_profile import UserProfileUpdateView, UserProfileView
from .user_settings import (
    UserSettingsNotificationsTestView,
    UserSettingsUpdateView,
    UserSettingsView,
)
from .wishlist.wishlist import WishlistView
