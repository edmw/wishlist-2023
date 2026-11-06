"""Tests for the access of users who have accepted a wishlist invitation.

Accepting an invitation grants no additional rights (see ADR-1000): the
invitee can do what any other user may do based on the list's visibility —
view it, favorite it and reserve wishes from it — but nothing more. Private
lists remain inaccessible without an invitation.
"""

from http import HTTPStatus

import pytest
from django.test import Client
from django.urls import reverse
from django.utils.translation import gettext_noop

from core import constants
from core.models import Favorite, Reservation, User, Wishlist, WishlistInvitation
from core.models.types import ItemOrdering, Visibility
from core.services import InvitationService, TemplatedNotification
from core.tests.conftest import CoreFixture

INVITEE_EMAIL = "carol@localhost"

INVITATION_EMAIL = TemplatedNotification(
    subject=gettext_noop("Invitation to a wish list"),
    template_name="email/invitation_wishlist.txt",
    html_template_name="email/invitation_wishlist.html",
)


def _users_list(owner: User) -> Wishlist:
    return Wishlist.objects.create(
        owner=owner,
        name_field="Users list",
        description_field="",
        visibility_field=Visibility.USERS,
        item_ordering_field=ItemOrdering.NAME_ASCENDING,
    )


def _private_list(owner: User) -> Wishlist:
    return Wishlist.objects.create(
        owner=owner,
        name_field="Private list",
        description_field="",
        visibility_field=Visibility.PRIVATE,
        item_ordering_field=ItemOrdering.NAME_ASCENDING,
    )


@pytest.mark.django_db
class TestInvitedUserAccess:
    def _accept_invitation(self, core: CoreFixture, wishlist: Wishlist) -> WishlistInvitation:
        """Creates a sent invitation for the list and accepts it as carol."""
        invitation = InvitationService.create_invitation(
            wishlist=wishlist,
            inviter=core.user_alice,
            invitee_email=INVITEE_EMAIL,
        )
        InvitationService.send_invitation(invitation=invitation, email=INVITATION_EMAIL)
        InvitationService.accept_invitation(code=str(invitation.code), user=core.user_carol)
        return invitation

    def test_can_view_users_list(self, core: CoreFixture, client: Client) -> None:
        """An invited user can view a list that is visible to all users."""
        wishlist = _users_list(core.user_alice)
        self._accept_invitation(core, wishlist)
        client.force_login(core.user_carol)

        response = client.get(reverse(constants.VIEW_WISHLIST, kwargs={constants.LIST_ID_KEY: wishlist.id}))
        assert response.status_code == HTTPStatus.OK

    def test_can_view_public_list(self, core: CoreFixture, client: Client) -> None:
        """An invited user can view a public list."""
        self._accept_invitation(core, core.list_alice)
        client.force_login(core.user_carol)

        response = client.get(
            reverse(constants.VIEW_WISHLIST, kwargs={constants.LIST_ID_KEY: core.list_alice.id})
        )
        assert response.status_code == HTTPStatus.OK

    def test_can_favorite_list(self, core: CoreFixture, client: Client) -> None:
        """An invited user can favorite the list."""
        wishlist = _users_list(core.user_alice)
        self._accept_invitation(core, wishlist)
        client.force_login(core.user_carol)

        response = client.post(
            reverse(constants.VIEW_FAVORITE_CREATE, kwargs={constants.USER_ID_KEY: core.user_carol.id}),
            data={"wishlist": str(wishlist.id)},
        )

        assert response.status_code == HTTPStatus.FOUND
        assert Favorite.objects.filter(user=core.user_carol, wishlist=wishlist).exists()

    def test_can_reserve_wish(self, core: CoreFixture, client: Client) -> None:
        """An invited user can reserve a wish from the list."""
        self._accept_invitation(core, core.list_alice)
        client.force_login(core.user_carol)

        url = (
            reverse(
                constants.VIEW_RESERVATION_CREATE,
                kwargs={constants.USER_ID_KEY: core.user_carol.id},
            )
            + f"?{constants.ITEM_ID_KEY}={core.item_alice.id}"
        )
        response = client.post(url, data={"wish": str(core.item_alice.id)})

        assert response.status_code == HTTPStatus.FOUND
        assert Reservation.objects.filter(holder=core.user_carol, wish=core.item_alice).exists()

    def test_has_no_editor_access(self, core: CoreFixture, client: Client) -> None:
        """An invited user cannot edit the list or its wishes."""
        wishlist = _users_list(core.user_alice)
        self._accept_invitation(core, wishlist)
        client.force_login(core.user_carol)

        kwargs = {constants.USER_ID_KEY: core.user_alice.id, constants.LIST_ID_KEY: wishlist.id}
        for view_name in (constants.VIEW_LIST_UPDATE, constants.VIEW_ITEM_CREATE):
            response = client.get(reverse(view_name, kwargs=kwargs))
            assert response.status_code == HTTPStatus.FORBIDDEN

    def test_private_list_stays_inaccessible_without_invitation(
        self, core: CoreFixture, client: Client
    ) -> None:
        """A private list cannot be viewed without an invitation."""
        wishlist = _private_list(core.user_alice)
        client.force_login(core.user_carol)

        response = client.get(reverse(constants.VIEW_WISHLIST, kwargs={constants.LIST_ID_KEY: wishlist.id}))
        assert response.status_code == HTTPStatus.FORBIDDEN
