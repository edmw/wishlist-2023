from dataclasses import dataclass
from uuid import UUID

import pytest
from django.core.management import call_command

from core.models import Favorite, Reservation, User, Wish, Wishlist
from core.tests import constants


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):  # noqa
    with django_db_blocker.unblock():
        call_command("loaddata", "testing.yaml")


@dataclass(frozen=True)
class CoreFixture:
    null_id: UUID
    super_user: User
    staff_user: User
    user_alice: User
    user_bob: User
    user_carol: User
    user_david: User
    user_elmo: User
    list_alice: Wishlist
    list_alice_empty: Wishlist
    list_bob: Wishlist
    item_alice: Wish
    item_alice_reserved: Wish
    favorite_alice: Favorite
    reservation_alice: Reservation


@pytest.fixture(scope="session")
def core(django_db_setup, django_db_blocker):  # noqa
    with django_db_blocker.unblock():
        return CoreFixture(
            null_id=UUID(int=0),
            super_user=User.objects.get(pk=constants.USER_ID_ALICE),
            staff_user=User.objects.get(pk=constants.USER_ID_BOB),
            user_alice=User.objects.get(pk=constants.USER_ID_ALICE),
            user_bob=User.objects.get(pk=constants.USER_ID_BOB),
            user_carol=User.objects.get(pk=constants.USER_ID_CAROL),
            user_david=User.objects.get(pk=constants.USER_ID_DAVID),
            user_elmo=User.objects.get(pk=constants.USER_ID_ELMO),
            list_alice=Wishlist.objects.get(pk=constants.LIST_ID_ALICE),
            list_alice_empty=Wishlist.objects.get(pk=constants.LIST_ID_ALICE_EMPTY),
            list_bob=Wishlist.objects.get(pk=constants.LIST_ID_BOB),
            item_alice=Wish.objects.get(pk=constants.ITEM_ID_ALICE),
            item_alice_reserved=Wish.objects.get(pk=constants.ITEM_ID_ALICE_RESERVED),
            favorite_alice=Favorite.objects.get(pk=constants.FAVORITE_ID_ALICE),
            reservation_alice=Reservation.objects.get(pk=constants.RESERVATION_ID_ALICE),
        )
