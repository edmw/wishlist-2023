from http import HTTPStatus
from typing import cast

import pytest
from django.http import HttpResponse
from django.test import Client
from django.urls import reverse

from core import constants
from core.models import UserID, WishlistID, WishlistMembership
from core.models.types import WishlistMembershipID
from core.services import WishlistCollaborationService
from core.tests._base import AssertLoggingMixin
from core.tests.conftest import CoreFixture


@pytest.mark.django_db
class TestMembershipDeleteView(AssertLoggingMixin):
    def _get_delete(
        self,
        client: Client,
        user_id: UserID,
        list_id: WishlistID,
        membership_id: WishlistMembershipID,
    ) -> HttpResponse:
        response = client.get(
            reverse(
                constants.VIEW_MEMBERSHIP_DELETE,
                kwargs={
                    constants.USER_ID_KEY: user_id,
                    constants.LIST_ID_KEY: list_id,
                    constants.MEMBERSHIP_ID_KEY: membership_id,
                },
            )
        )
        return cast(HttpResponse, response)

    def _post_delete(
        self,
        client: Client,
        user_id: UserID,
        list_id: WishlistID,
        membership_id: WishlistMembershipID,
    ) -> HttpResponse:
        response = client.post(
            reverse(
                constants.VIEW_MEMBERSHIP_DELETE,
                kwargs={
                    constants.USER_ID_KEY: user_id,
                    constants.LIST_ID_KEY: list_id,
                    constants.MEMBERSHIP_ID_KEY: membership_id,
                },
            )
        )
        return cast(HttpResponse, response)

    def test_membership_delete_view_ok(self, core: CoreFixture, client: Client) -> None:
        client.force_login(core.user_alice)
        WishlistCollaborationService.add_editor(wishlist=core.list_alice, user=core.user_bob)
        membership = WishlistMembership.objects.get(wishlist=core.list_alice, user=core.user_bob)

        response = self._get_delete(client, core.user_alice.id, core.list_alice.id, membership.id)

        assert response.status_code == HTTPStatus.OK
        content = response.content.decode("utf-8")
        assert "remove" in content
        assert "bob" in content
        assert "Wishes for Alice" in content

        response = self._post_delete(client, core.user_alice.id, core.list_alice.id, membership.id)

        assert response.status_code == HTTPStatus.FOUND
        assert response.headers["Location"] == reverse(
            constants.VIEW_MEMBERSHIPS,
            kwargs={
                constants.USER_ID_KEY: core.user_alice.id,
                constants.LIST_ID_KEY: core.list_alice.id,
            },
        )
        assert not WishlistMembership.objects.filter(pk=membership.id).exists()

    def test_membership_delete_view_other_list(self, core: CoreFixture, client: Client) -> None:
        client.force_login(core.user_alice)
        WishlistCollaborationService.add_editor(wishlist=core.list_bob, user=core.user_carol)
        membership = WishlistMembership.objects.get(wishlist=core.list_bob, user=core.user_carol)

        assert (
            self._get_delete(client, core.user_alice.id, core.list_alice.id, membership.id).status_code
            == HTTPStatus.NOT_FOUND
        )
        assert (
            self._post_delete(client, core.user_alice.id, core.list_alice.id, membership.id).status_code
            == HTTPStatus.NOT_FOUND
        )
        assert WishlistMembership.objects.filter(pk=membership.id).exists()

    def test_membership_delete_view_invalid_membership(self, core: CoreFixture, client: Client) -> None:
        client.force_login(core.user_alice)
        membership_id = cast(WishlistMembershipID, core.null_id)

        assert (
            self._get_delete(client, core.user_alice.id, core.list_alice.id, membership_id).status_code
            == HTTPStatus.NOT_FOUND
        )
        assert (
            self._post_delete(client, core.user_alice.id, core.list_alice.id, membership_id).status_code
            == HTTPStatus.NOT_FOUND
        )

    def test_membership_delete_view_not_allowed(
        self, core: CoreFixture, client: Client, caplog: pytest.LogCaptureFixture
    ) -> None:
        client.force_login(core.user_bob)
        WishlistCollaborationService.add_editor(wishlist=core.list_alice, user=core.user_carol)
        membership = WishlistMembership.objects.get(wishlist=core.list_alice, user=core.user_carol)

        assert (
            self._get_delete(client, core.user_alice.id, core.list_alice.id, membership.id).status_code
            == HTTPStatus.FORBIDDEN
        )
        self.assert_log_permission_denied_other_user(caplog)
        assert (
            self._post_delete(client, core.user_alice.id, core.list_alice.id, membership.id).status_code
            == HTTPStatus.FORBIDDEN
        )
        self.assert_log_permission_denied_other_user(caplog)
        assert WishlistMembership.objects.filter(pk=membership.id).exists()

    def test_membership_delete_view_unauthenticated(self, core: CoreFixture, client: Client) -> None:
        WishlistCollaborationService.add_editor(wishlist=core.list_alice, user=core.user_bob)
        membership = WishlistMembership.objects.get(wishlist=core.list_alice, user=core.user_bob)

        assert (
            self._get_delete(client, core.user_alice.id, core.list_alice.id, membership.id).status_code
            == HTTPStatus.FOUND
        )
        assert (
            self._post_delete(client, core.user_alice.id, core.list_alice.id, membership.id).status_code
            == HTTPStatus.FOUND
        )
