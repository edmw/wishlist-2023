"""The Core’s constants."""

from typing import Final

USER_ID_KEY: Final[str] = "user_id"
LIST_ID_KEY: Final[str] = "list_id"
ITEM_ID_KEY: Final[str] = "item_id"
FAVORITE_ID_KEY: Final[str] = "favorite_id"
RESERVATION_ID_KEY: Final[str] = "reservation_id"
MEMBERSHIP_ID_KEY: Final[str] = "membership_id"

VIEW_USER_PROFILE: Final[str] = "user-profile"
VIEW_USER_PROFILE_UPDATE: Final[str] = "user-profile-update"
VIEW_USER_SETTINGS: Final[str] = "user-settings"
VIEW_USER_SETTINGS_UPDATE: Final[str] = "user-settings-update"
VIEW_USER_SETTINGS_NOTIFICATION_TEST: Final[str] = "user-settings-notifications-test"
VIEW_LISTS: Final[str] = "lists"
VIEW_LIST_CREATE: Final[str] = "list-create"
VIEW_LIST_UPDATE: Final[str] = "list-update"
VIEW_LIST_DELETE: Final[str] = "list-delete"
VIEW_LIST_SHARE: Final[str] = "list-share"
VIEW_LIST_EXPORT: Final[str] = "list-export"
VIEW_MEMBERSHIPS: Final[str] = "memberships"
VIEW_MEMBERSHIP_DELETE: Final[str] = "membership-delete"
VIEW_ITEMS: Final[str] = "items"
VIEW_ITEM_CREATE: Final[str] = "item-create"
VIEW_ITEM_UPDATE: Final[str] = "item-update"
VIEW_ITEM_MOVE: Final[str] = "item-move"
VIEW_ITEM_ARCHIVE: Final[str] = "item-archive"
VIEW_ITEM_UNARCHIVE: Final[str] = "item-unarchive"
VIEW_ITEM_RELEASE: Final[str] = "item-release"
VIEW_ITEM_RECEIVE: Final[str] = "item-receive"
VIEW_ITEM_DELETE: Final[str] = "item-delete"
VIEW_ITEM_MANAGE: Final[str] = "item-manage"
VIEW_FAVORITES: Final[str] = "favorites"
VIEW_FAVORITE_CREATE: Final[str] = "favorite-create"
VIEW_FAVORITE_DELETE: Final[str] = "favorite-delete"
VIEW_FAVORITE_UPDATE: Final[str] = "favorite-update"
VIEW_WISHLIST: Final[str] = "wishlist"
VIEW_RESERVATION_CREATE: Final[str] = "reservation-create"
VIEW_RESERVATION_UNDO: Final[str] = "reservation-undo"

ONE_MINUTE_IN_SECONDS: Final[int] = 60
TWO_MINUTES_IN_SECONDS: Final[int] = 2 * ONE_MINUTE_IN_SECONDS
ONE_HOUR_IN_SECONDS: Final[int] = 60 * ONE_MINUTE_IN_SECONDS
TWO_HOURS_IN_SECONDS: Final[int] = 2 * ONE_HOUR_IN_SECONDS
ONE_DAY_IN_SECONDS: Final[int] = 24 * ONE_HOUR_IN_SECONDS
