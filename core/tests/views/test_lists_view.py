from http import HTTPStatus

import pytest
from django.http import HttpResponse
from django.test import Client
from django.urls import reverse

from core import constants
from core.models import UserID
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
        return response

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
