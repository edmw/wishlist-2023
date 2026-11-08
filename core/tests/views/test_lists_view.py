from http import HTTPStatus
from typing import cast

import pytest
from django.http import HttpResponse
from django.test import Client
from django.urls import reverse

from core import constants
from core.models import UserID, Wishlist
from core.models.types import Visibility
from core.services import WishlistCollaborationService
from core.tests._base import AssertLoggingMixin
from core.tests.conftest import CoreFixture


@pytest.mark.django_db
class TestListsView(AssertLoggingMixin):
    """Test for the permissions on lists views: Checks if entitled users
    are able to access the views, others not.
    """

    def _get(self, client: Client, user_id: UserID) -> HttpResponse:
        response = client.get(
            reverse(
                constants.VIEW_LISTS,
                kwargs={constants.USER_ID_KEY: user_id},
            )
        )
        return cast(HttpResponse, response)

    def test_lists_view_ok(self, core: CoreFixture, client: Client) -> None:
        """Alice requesting alice’s wish lists."""
        client.force_login(core.user_alice)
        assert self._get(client, core.user_alice.id).status_code == HTTPStatus.OK

    def test_lists_view_contains_collaborated_wishlist(self, core: CoreFixture, client: Client) -> None:
        client.force_login(core.user_bob)
        WishlistCollaborationService.add_editor(wishlist=core.list_alice, user=core.user_bob)

        response = self._get(client, core.user_bob.id)

        assert response.status_code == HTTPStatus.OK
        assert "Wishes for Bob" in response.content.decode("utf-8")
        assert "Wishes for Alice" in response.content.decode("utf-8")
        assert "shared by alice" in response.content.decode("utf-8")

    def test_lists_view_shows_membership_action_for_owner_list_with_memberships(
        self, core: CoreFixture, client: Client
    ) -> None:
        client.force_login(core.user_alice)
        WishlistCollaborationService.add_editor(wishlist=core.list_alice, user=core.user_bob)

        response = self._get(client, core.user_alice.id)

        assert response.status_code == HTTPStatus.OK
        memberships_url = reverse(
            constants.VIEW_MEMBERSHIPS,
            kwargs={
                constants.USER_ID_KEY: core.user_alice.id,
                constants.LIST_ID_KEY: core.list_alice.id,
            },
        )
        assert memberships_url in response.content.decode("utf-8")

    def test_lists_view_hides_membership_action_for_owner_list_without_memberships(
        self, core: CoreFixture, client: Client
    ) -> None:
        client.force_login(core.user_alice)

        response = self._get(client, core.user_alice.id)

        assert response.status_code == HTTPStatus.OK
        memberships_url = reverse(
            constants.VIEW_MEMBERSHIPS,
            kwargs={
                constants.USER_ID_KEY: core.user_alice.id,
                constants.LIST_ID_KEY: core.list_alice.id,
            },
        )
        assert memberships_url not in response.content.decode("utf-8")

    def test_lists_view_shows_share_action_for_shareable_wishlist(
        self, core: CoreFixture, client: Client
    ) -> None:
        """The share action is shown for wish lists that are not private."""
        client.force_login(core.user_alice)

        response = self._get(client, core.user_alice.id)

        assert response.status_code == HTTPStatus.OK
        content = response.content.decode("utf-8")
        assert core.list_alice.get_absolute_share_url() in content
        # Every row renders the share slot so that titles stay aligned.
        count = content.count('class="wl-share"')
        assert count == response.context["your_wishlists_count"]  # type: ignore[attr-defined]

    def test_lists_view_hides_share_action_for_private_wishlist(
        self, core: CoreFixture, client: Client
    ) -> None:
        """The share action is not shown for private wish lists."""
        client.force_login(core.user_alice)
        list_alice = Wishlist.objects.get(pk=core.list_alice.pk)
        list_alice.visibility_field = Visibility.PRIVATE
        list_alice.save(update_fields=[Wishlist.Fields.VISIBILITY])

        response = self._get(client, core.user_alice.id)

        assert response.status_code == HTTPStatus.OK
        content = response.content.decode("utf-8")
        assert core.list_alice.get_absolute_share_url() not in content
        # The share slot is still rendered (empty) so that titles stay aligned.
        assert '<span class="wl-share"></span>' in content
        count = content.count('class="wl-share"')
        assert count == response.context["your_wishlists_count"]  # type: ignore[attr-defined]

    def test_lists_view_not_allowed(
        self, core: CoreFixture, client: Client, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Bob requesting alice’s wish lists."""
        client.force_login(core.user_bob)
        assert self._get(client, core.user_alice.id).status_code == HTTPStatus.FORBIDDEN
        self.assert_log_permission_denied_other_user(caplog)

    def test_lists_view_unauthenticated(self, core: CoreFixture, client: Client) -> None:
        """Anonymous requesting alice’s wish lists."""
        assert self._get(client, core.user_alice.id).status_code == HTTPStatus.FOUND
