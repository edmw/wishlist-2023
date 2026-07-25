"""The Core’s routes.

These url patterns are included in the root url patterns of the webapp.
"""

from django.urls import path
from django.urls.resolvers import URLPattern

from core import constants
from core.views import (
    FavoriteCreateView,
    FavoriteDeleteView,
    FavoritesView,
    FavoriteUpdateView,
    ItemArchiveView,
    ItemCreateView,
    ItemDeleteView,
    ItemManageView,
    ItemMoveView,
    ItemReceiveView,
    ItemReleaseView,
    ItemsView,
    ItemUnarchiveView,
    ItemUpdateView,
    LegalNoticeView,
    ListCreateView,
    ListDeleteView,
    ListExportView,
    ListsView,
    ListUpdateView,
    MembershipDeleteView,
    MembershipsView,
    PrivacyPolicyView,
    ReservationCreateView,
    ReservationUndoView,
    StartView,
    UserProfileUpdateView,
    UserProfileView,
    UserSettingsNotificationsTestView,
    UserSettingsUpdateView,
    UserSettingsView,
    WishlistView,
)

pages_user: list[URLPattern] = [
    path(
        f"user/<b62uuid:{constants.USER_ID_KEY}>",
        UserProfileView.as_view(),
        name=constants.VIEW_USER_PROFILE,
    ),
    path(
        f"user/<b62uuid:{constants.USER_ID_KEY}>/edit",
        UserProfileUpdateView.as_view(),
        name=constants.VIEW_USER_PROFILE_UPDATE,
    ),
    path(
        f"user/<b62uuid:{constants.USER_ID_KEY}>/settings",
        UserSettingsView.as_view(),
        name=constants.VIEW_USER_SETTINGS,
    ),
    path(
        f"user/<b62uuid:{constants.USER_ID_KEY}>/settings/update",
        UserSettingsUpdateView.as_view(),
        name=constants.VIEW_USER_SETTINGS_UPDATE,
    ),
    path(
        f"user/<b62uuid:{constants.USER_ID_KEY}>/settings/notifications/test",
        UserSettingsNotificationsTestView.as_view(),
        name=constants.VIEW_USER_SETTINGS_NOTIFICATION_TEST,
    ),
]
pages_user_lists: list[URLPattern] = [
    path(
        f"user/<b62uuid:{constants.USER_ID_KEY}>/lists",
        ListsView.as_view(),
        name=constants.VIEW_LISTS,
    ),
    path(
        f"user/<b62uuid:{constants.USER_ID_KEY}>/lists/create",
        ListCreateView.as_view(),
        name=constants.VIEW_LIST_CREATE,
    ),
    path(
        f"user/<b62uuid:{constants.USER_ID_KEY}>/lists/<b62uuid:{constants.LIST_ID_KEY}>/update",
        ListUpdateView.as_view(),
        name=constants.VIEW_LIST_UPDATE,
    ),
    path(
        f"user/<b62uuid:{constants.USER_ID_KEY}>/lists/<b62uuid:{constants.LIST_ID_KEY}>/delete",
        ListDeleteView.as_view(),
        name=constants.VIEW_LIST_DELETE,
    ),
    path(
        f"user/<b62uuid:{constants.USER_ID_KEY}>/lists/<b62uuid:{constants.LIST_ID_KEY}>/export",
        ListExportView.as_view(),
        name=constants.VIEW_LIST_EXPORT,
    ),
]
pages_user_items: list[URLPattern] = [
    path(
        f"user/<b62uuid:{constants.USER_ID_KEY}>/lists/<b62uuid:{constants.LIST_ID_KEY}>/items",
        ItemsView.as_view(),
        name=constants.VIEW_ITEMS,
    ),
    path(
        f"user/<b62uuid:{constants.USER_ID_KEY}>/lists/<b62uuid:{constants.LIST_ID_KEY}>/items/create",
        ItemCreateView.as_view(),
        name=constants.VIEW_ITEM_CREATE,
    ),
    path(
        (
            f"user/<b62uuid:{constants.USER_ID_KEY}>/"
            f"lists/<b62uuid:{constants.LIST_ID_KEY}>/"
            f"items/<b62uuid:{constants.ITEM_ID_KEY}>/update"
        ),
        ItemUpdateView.as_view(),
        name=constants.VIEW_ITEM_UPDATE,
    ),
    path(
        (
            f"user/<b62uuid:{constants.USER_ID_KEY}>/"
            f"lists/<b62uuid:{constants.LIST_ID_KEY}>/"
            f"items/<b62uuid:{constants.ITEM_ID_KEY}>/move"
        ),
        ItemMoveView.as_view(),
        name=constants.VIEW_ITEM_MOVE,
    ),
    path(
        (
            f"user/<b62uuid:{constants.USER_ID_KEY}>/"
            f"lists/<b62uuid:{constants.LIST_ID_KEY}>/"
            f"items/<b62uuid:{constants.ITEM_ID_KEY}>/archive"
        ),
        ItemArchiveView.as_view(),
        name=constants.VIEW_ITEM_ARCHIVE,
    ),
    path(
        (
            f"user/<b62uuid:{constants.USER_ID_KEY}>/"
            f"lists/<b62uuid:{constants.LIST_ID_KEY}>/"
            f"items/<b62uuid:{constants.ITEM_ID_KEY}>/unarchive"
        ),
        ItemUnarchiveView.as_view(),
        name=constants.VIEW_ITEM_UNARCHIVE,
    ),
    path(
        (
            f"user/<b62uuid:{constants.USER_ID_KEY}>/"
            f"lists/<b62uuid:{constants.LIST_ID_KEY}>/"
            f"items/<b62uuid:{constants.ITEM_ID_KEY}>/release"
        ),
        ItemReleaseView.as_view(),
        name=constants.VIEW_ITEM_RELEASE,
    ),
    path(
        (
            f"user/<b62uuid:{constants.USER_ID_KEY}>/"
            f"lists/<b62uuid:{constants.LIST_ID_KEY}>/"
            f"items/<b62uuid:{constants.ITEM_ID_KEY}>/receive"
        ),
        ItemReceiveView.as_view(),
        name=constants.VIEW_ITEM_RECEIVE,
    ),
    path(
        (
            f"user/<b62uuid:{constants.USER_ID_KEY}>/"
            f"lists/<b62uuid:{constants.LIST_ID_KEY}>/"
            f"items/<b62uuid:{constants.ITEM_ID_KEY}>/delete"
        ),
        ItemDeleteView.as_view(),
        name=constants.VIEW_ITEM_DELETE,
    ),
    path(
        (
            f"user/<b62uuid:{constants.USER_ID_KEY}>/"
            f"lists/<b62uuid:{constants.LIST_ID_KEY}>/"
            f"items/<b62uuid:{constants.ITEM_ID_KEY}>/manage"
        ),
        ItemManageView.as_view(),
        name=constants.VIEW_ITEM_MANAGE,
    ),
]
pages_user_memberships: list[URLPattern] = [
    path(
        f"user/<b62uuid:{constants.USER_ID_KEY}>/lists/<b62uuid:{constants.LIST_ID_KEY}>/memberships",
        MembershipsView.as_view(),
        name=constants.VIEW_MEMBERSHIPS,
    ),
    path(
        (
            f"user/<b62uuid:{constants.USER_ID_KEY}>/"
            f"lists/<b62uuid:{constants.LIST_ID_KEY}>/"
            f"memberships/<b62uuid:{constants.MEMBERSHIP_ID_KEY}>/delete"
        ),
        MembershipDeleteView.as_view(),
        name=constants.VIEW_MEMBERSHIP_DELETE,
    ),
]
pages_user_favorites: list[URLPattern] = [
    path(
        f"user/<b62uuid:{constants.USER_ID_KEY}>/favorites",
        FavoritesView.as_view(),
        name=constants.VIEW_FAVORITES,
    ),
    path(
        f"user/<b62uuid:{constants.USER_ID_KEY}>/favorites/create",
        FavoriteCreateView.as_view(),
        name=constants.VIEW_FAVORITE_CREATE,
    ),
    path(
        f"user/<b62uuid:{constants.USER_ID_KEY}>/favorites/<b62uuid:{constants.FAVORITE_ID_KEY}>/delete",
        FavoriteDeleteView.as_view(),
        name=constants.VIEW_FAVORITE_DELETE,
    ),
    path(
        f"user/<b62uuid:{constants.USER_ID_KEY}>/favorites/<b62uuid:{constants.FAVORITE_ID_KEY}>/update",
        FavoriteUpdateView.as_view(),
        name=constants.VIEW_FAVORITE_UPDATE,
    ),
]
pages_wishlist: list[URLPattern] = [
    path(
        f"list/<b62uuid:{constants.LIST_ID_KEY}>",
        WishlistView.as_view(),
        name=constants.VIEW_WISHLIST,
    ),
]
pages_reservations: list[URLPattern] = [
    path(
        f"user/<b62uuid:{constants.USER_ID_KEY}>/reservations/create",
        ReservationCreateView.as_view(),
        name=constants.VIEW_RESERVATION_CREATE,
    ),
    path(
        (
            f"user/<b62uuid:{constants.USER_ID_KEY}>/"
            f"reservations/<b62uuid:{constants.RESERVATION_ID_KEY}>/undo"
        ),
        ReservationUndoView.as_view(),
        name=constants.VIEW_RESERVATION_UNDO,
    ),
]
pages = (
    pages_user
    + pages_user_lists
    + pages_user_items
    + pages_user_memberships
    + pages_user_favorites
    + pages_wishlist
    + pages_reservations
)

pages_public = [
    path("", StartView.as_view(), name="start"),
    path("legal-notice", LegalNoticeView.as_view(), name="legal-notice"),
    path("privacy-policy", PrivacyPolicyView.as_view(), name="privacy-policy"),
]

urlpatterns: list[URLPattern] = pages + pages_public
