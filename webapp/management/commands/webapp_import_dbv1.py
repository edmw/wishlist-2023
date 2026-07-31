# Historical command for importing a legacy dataset. Kept for archival and reference only.
# type: ignore
"""Import DBv1 command."""

import json
from collections import namedtuple
from typing import Any, TypeAlias
from uuid import UUID

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import CommandParser
from django.utils import timezone
from mysql import connector as mysql
from mysql.connector.abstracts import MySQLConnectionAbstract
from mysql.connector.pooling import PooledMySQLConnection

from core.models import (
    Description,
    Favorite,
    ItemOrdering,
    Name,
    Preference,
    Reference,
    ReferencePhoto,
    Reservation,
    User,
    Visibility,
    Wish,
    WishID,
    Wishlist,
    WishlistID,
)
from core.models.favorite_factory import FavoriteFactory
from core.models.reservation_factory import ReservationFactory
from core.models.wish_factory import WishFactory
from core.models.wishlist_factory import WishlistFactory
from core.services import (
    FavoriteService,
    ReservationService,
    UserService,
    WishlistService,
    WishService,
)

from ._base import WebappBaseCommand

MySQLConnectionType: TypeAlias = MySQLConnectionAbstract | PooledMySQLConnection


V1User = namedtuple(
    "V1User",
    [
        "id",
        "identifier",
        "email",
        "fullName",
        "firstName",
        "lastName",
        "language",
        "picture",
        "firstLogin",
        "lastLogin",
        "confidant",
        "identity",
        "nickName",
        "settings",
        "identityProvider",
    ],
)

V1List = namedtuple(
    "V1List",
    [
        "id",
        "title",
        "visibility",
        "createdAt",
        "modifiedAt",
        "userID",
        "itemsSorting",
        "options",
    ],
)

V1Item = namedtuple(
    "V1Item",
    [
        "id",
        "title",
        "text",
        "url",
        "imageUrl",
        "createdAt",
        "modifiedAt",
        "localImageUrl",
        "listID",
        "preference",
        "archival",
    ],
)


V1Favorite = namedtuple(
    "V1Favorite",
    [
        "id",
        "userID",
        "listID",
        "notifications",
    ],
)


V1Reservation = namedtuple(
    "V1Reservation",
    [
        "id",
        "createdAt",
        "itemID",
        "holder",
        "status",
    ],
)


MAP_VISIBILITY = {
    0: Visibility.PRIVATE,
    1: Visibility.PUBLIC,
    2: Visibility.USERS,
}


def map_visibility(v1_visibility: int) -> Visibility:
    return Visibility(MAP_VISIBILITY.get(v1_visibility, Visibility.PRIVATE))


MAP_ITEMORDERING = {
    "+name": ItemOrdering.NAME_ASCENDING,
    "-name": ItemOrdering.NAME_DESCENDING,
    "+preference": ItemOrdering.PREFERENCE_ASCENDING,
    "-preference": ItemOrdering.PREFERENCE_DESCENDING,
    "+createdAt": ItemOrdering.CREATED_AT_ASCENDING,
    "-createdAt": ItemOrdering.CREATED_AT_DESCENDING,
}


def map_itemordering(v1_itemssorting: str) -> ItemOrdering:
    return ItemOrdering(MAP_ITEMORDERING.get(v1_itemssorting, ItemOrdering.NAME_ASCENDING))


MAP_PREFERENCE = {
    -2: Preference.LOWEST,
    -1: Preference.LOW,
    0: Preference.NEUTRAL,
    1: Preference.HIGH,
    2: Preference.HIGHEST,
}


def map_preference(v1_preference: int) -> Preference:
    return Preference(MAP_PREFERENCE.get(v1_preference, Preference.NEUTRAL))


class Command(WebappBaseCommand):
    """Import DBv1 command: Import data from Wishlist webapp version 1."""

    help = "Import data from Wishlist webapp version 1"

    def add_arguments(self, parser: CommandParser) -> None:
        """Adds arguments for import."""
        parser.add_argument(
            "--host",
            required=True,
            help="Host for source database.",
        )
        parser.add_argument(
            "--port",
            help="Port for source database.",
            type=int,
            default=3306,
        )
        parser.add_argument(
            "--name",
            required=True,
            help="Name for source database.",
        )
        parser.add_argument(
            "--user",
            required=True,
            help="User for source database.",
        )
        parser.add_argument(
            "--password",
            required=True,
            help="Password for source database.",
        )
        parser.add_argument(
            "--disable-ssl",
            default=False,
            action="store_true",
            help="Disable SSL connection.",
        )
        parser.add_argument(
            "--ignore-users-with-email",
            nargs="*",
            help="Do not import users with any of the emails given.",
        )
        super().add_arguments(parser=parser)

    def select_users(
        self,
        connection: MySQLConnectionType,
    ) -> list[V1User]:
        sql = "select * from User"
        with connection.cursor() as cursor:
            v1_users = []
            cursor.execute(sql)
            result = cursor.fetchall()
            for row in result:
                data = list(row)
                data[0] = UUID(bytes=bytes(data[0]))
                data[1] = UUID(bytes=bytes(data[1]))
                v1_user = V1User(*data)
                v1_users.append(v1_user)
            return v1_users

    def map_users(self, v1_users: list[V1User], ignore_users_with_email: list[str]) -> dict[UUID, User]:
        v1_user_map = {}
        for v1_user in v1_users:
            email = v1_user.email
            if user := UserService.find_user_for_email(email=email):
                v1_user_map[v1_user.id] = user
            else:
                if email not in ignore_users_with_email:
                    raise ObjectDoesNotExist(f"User with email '{email}' not found")
        return v1_user_map

    def map_holders(self, v1_users: list[V1User], ignore_users_with_email: list[str]) -> dict[UUID, User]:
        v1_holders_map = {}
        for v1_user in v1_users:
            email = v1_user.email
            if user := UserService.find_user_for_email(email=email):
                v1_holders_map[v1_user.identifier] = user
            else:
                if email not in ignore_users_with_email:
                    raise ObjectDoesNotExist(f"User with email '{email}' not found")
        return v1_holders_map

    def select_lists_for_user(self, connection: MySQLConnectionType, v1_user: V1User) -> list[V1List]:
        sql = "select * from List where BINARY userID=%s"
        with connection.cursor() as cursor:
            v1_lists = []
            cursor.execute(sql, (v1_user.id.bytes,))
            result = cursor.fetchall()
            for row in result:
                data = list(row)
                data[0] = UUID(bytes=bytes(data[0]))
                data[5] = UUID(bytes=bytes(data[5]))
                v1_list = V1List(*data)
                v1_lists.append(v1_list)
            return v1_lists

    def make_list(self, v1_list: V1List, *, user: User) -> Wishlist:
        try:
            return WishlistService.get_wishlist(id=v1_list.id)
        except Wishlist.DoesNotExist:
            wishlist = WishlistFactory.create(
                id=v1_list.id,
                name=Name(v1_list.title),
                description=Description(""),
                owner=user,
                visibility=map_visibility(v1_list.visibility),
                item_ordering=map_itemordering(v1_list.itemsSorting),
                mask_reservations=v1_list.options != 0,
            )
            wishlist.save()
            print(f"created {wishlist!r}")
            return wishlist

    def select_items_for_list(self, connection: MySQLConnectionType, v1_list: V1List) -> list[V1Item]:
        sql = "select * from Item where BINARY listID=%s"
        with connection.cursor() as cursor:
            v1_items = []
            cursor.execute(sql, (v1_list.id.bytes,))
            result = cursor.fetchall()
            for row in result:
                data = list(row)
                data[0] = UUID(bytes=bytes(data[0]))
                data[8] = UUID(bytes=bytes(data[8]))
                v1_item = V1Item(*data)
                v1_items.append(v1_item)
            return v1_items

    def url_from_json(self, string: str | None) -> str:
        if string:
            data = json.loads(string)
            return data["relative"]
        return ""

    def make_item(self, v1_item: V1Item, *, wishlist: Wishlist, user: User) -> Wish:
        try:
            return WishService.get_wish(id=v1_item.id)
        except Wish.DoesNotExist:
            wish = WishFactory.create(
                id=v1_item.id,
                name=Name(v1_item.title),
                description=Description(v1_item.text),
                reference=Reference(self.url_from_json(v1_item.url)),
                reference_photo=ReferencePhoto(self.url_from_json(v1_item.imageUrl)),
                preference=map_preference(v1_item.preference),
                wishlist=wishlist,
                archived=v1_item.archival != 0,
                archived_at=timezone.now() if v1_item.archival != 0 else None,
            )
            wish.save(notify=False)
            print(f"created {wish!r}")
            return wish

    def select_favorites(self, connection: MySQLConnectionType) -> list[V1Favorite]:
        sql = "select * from Favorite"
        with connection.cursor() as cursor:
            v1_favorites = []
            cursor.execute(sql)
            result = cursor.fetchall()
            for row in result:
                data = list(row)
                data[0] = UUID(bytes=bytes(data[0]))
                data[1] = UUID(bytes=bytes(data[1]))
                data[2] = UUID(bytes=bytes(data[2]))
                v1_favorite = V1Favorite(*data)
                v1_favorites.append(v1_favorite)
            return v1_favorites

    def make_favorite(
        self, v1_favorite: V1Favorite, *, wishlists: dict[WishlistID, Wishlist], user: User
    ) -> Favorite | None:
        try:
            return FavoriteService.get_favorite(id=v1_favorite.id)
        except Favorite.DoesNotExist:
            if wishlist := wishlists.get(v1_favorite.listID):
                favorite = FavoriteFactory.create(
                    id=v1_favorite.id,
                    wishlist=wishlist,
                    user=user,
                    notify_on_item_create=v1_favorite.notifications != 0,
                )
                favorite.save()
                print(f"created {favorite!r}")
                return favorite
            return None

    def select_reservations(self, connection: MySQLConnectionType) -> list[V1Reservation]:
        sql = "select * from Reservation"
        with connection.cursor() as cursor:
            v1_reservations = []
            cursor.execute(sql)
            result = cursor.fetchall()
            for row in result:
                data = list(row)
                data[0] = UUID(bytes=bytes(data[0]))
                data[2] = UUID(bytes=bytes(data[2]))
                data[3] = UUID(bytes=bytes(data[3]))
                v1_reservation = V1Reservation(*data)
                v1_reservations.append(v1_reservation)
            return v1_reservations

    def make_reservation(
        self, v1_reservation: V1Reservation, *, wishes: dict[WishID, Wish], user: User
    ) -> Reservation | None:
        try:
            return ReservationService.get_reservation(id=v1_reservation.id)
        except Reservation.DoesNotExist:
            if wish := wishes.get(v1_reservation.itemID):
                reservation = ReservationFactory.create(
                    id=v1_reservation.id,
                    holder=user,
                    wish=wish,
                    completed=v1_reservation.status != 0,
                    completed_at=timezone.now() if v1_reservation.status != 0 else None,
                )
                reservation.save(notify=False)
                print(f"created {reservation!r}")
                return reservation
            return None

    def import_wishlists_and_wishes(
        self,
        v1_users: list[V1User],
        v1_users_map: dict[UUID, User],
        connection: MySQLConnectionType,
    ) -> tuple[dict[WishlistID, Wishlist], dict[WishID, Wish]]:
        """Imports all wish lists and wishes for all of the already existing
        users. Any wish list or wish owned by an unknown user will be skipped.
        Returns a collection of imported wish lists and a collection of imported
        wishes.
        """
        wishlists = {}
        wishes = {}
        for v1_user in v1_users:
            if user := v1_users_map.get(v1_user.id):
                v1_lists = self.select_lists_for_user(connection, v1_user)
                for v1_list in v1_lists:
                    wishlist = self.make_list(v1_list, user=user)
                    wishlists[wishlist.id] = wishlist
                    v1_items = self.select_items_for_list(connection, v1_list)
                    for v1_item in v1_items:
                        wish = self.make_item(v1_item, wishlist=wishlist, user=user)
                        wishes[wish.id] = wish
        return wishlists, wishes

    def import_favorites(
        self,
        wishlists: dict[WishlistID, Wishlist],
        v1_users_map: dict[UUID, User],
        connection: MySQLConnectionType,
    ) -> None:
        """Imports all reservations where the affected wish list was previously
        imported and where the favorite user is an already existing user.
        """
        v1_favorites = self.select_favorites(connection)
        for v1_favorite in v1_favorites:
            if user := v1_users_map.get(v1_favorite.userID):
                self.make_favorite(v1_favorite, wishlists=wishlists, user=user)

    def import_reservations(
        self,
        wishes: dict[WishID, Wish],
        v1_holders_map: dict[UUID, User],
        connection: MySQLConnectionType,
    ) -> None:
        """Imports all reservations where the affected wish was previously
        imported and where the reservation holder is an already existing user.
        """
        v1_reservations = self.select_reservations(connection)
        for v1_reservation in v1_reservations:
            if holder := v1_holders_map.get(v1_reservation.holder):
                self.make_reservation(v1_reservation, wishes=wishes, user=holder)

    def handle(self, *args: Any, **options: Any) -> None:
        self.banner(["WEBAPP IMPORT DBV1", self.help])

        try:
            with mysql.connect(
                host=options["host"],
                port=options["port"],
                user=options["user"],
                password=options["password"],
                database=options["name"],
                ssl_disabled=options["disable_ssl"],
            ) as connection:
                v1_users = self.select_users(connection)
                ignore_users_with_email = options.get("ignore_users_with_email") or []
                v1_users_map = self.map_users(v1_users, ignore_users_with_email)
                v1_holders_map = self.map_holders(v1_users, ignore_users_with_email)

                wishlists, wishes = self.import_wishlists_and_wishes(v1_users, v1_users_map, connection)
                self.import_favorites(wishlists, v1_users_map, connection)
                self.import_reservations(wishes, v1_holders_map, connection)

        except mysql.Error as mysql_error:
            self.banner(["MYSQL ERROR", str(mysql_error)])
        except ObjectDoesNotExist as object_does_not_exist:
            self.banner(["DJANGO MODEL", str(object_does_not_exist)])
