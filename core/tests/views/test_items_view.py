from http import HTTPStatus

import pytest
from django.http import HttpResponse
from django.test import Client
from django.urls import reverse

from core import constants
from core.models import UserID, WishlistID
from core.tests._base import AssertLoggingMixin
from core.tests.conftest import CoreFixture


@pytest.mark.django_db()
class TestItemsView(AssertLoggingMixin):
    def _get(self, client: Client, user_id: UserID, list_id: WishlistID) -> HttpResponse:
        response = client.get(
            reverse(
                constants.VIEW_ITEMS,
                kwargs={constants.USER_ID_KEY: user_id, constants.LIST_ID_KEY: list_id},
            )
        )
        return response

    def test_items_view_ok(self, core: CoreFixture, client: Client) -> None:
        """Alice requesting alice’s wish items."""
        client.force_login(core.user_alice)
        assert self._get(client, core.user_alice.id, core.list_alice.id).status_code == HTTPStatus.OK

    def test_items_view_not_allowed(
        self, core: CoreFixture, client: Client, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Bob requesting alice’s wish items."""
        client.force_login(core.user_bob)
        assert self._get(client, core.user_alice.id, core.list_alice.id).status_code == HTTPStatus.FORBIDDEN
        self.assert_log_permission_denied_other_user(caplog)
        assert self._get(client, core.user_bob.id, core.list_alice.id).status_code == HTTPStatus.FORBIDDEN
        self.assert_log_permission_denied_other_list(caplog)

    def test_items_view_unauthenticated(self, core: CoreFixture, client: Client) -> None:
        """Anonymous requesting alice’s wish items."""
        assert self._get(client, core.user_alice.id, core.list_alice.id).status_code == HTTPStatus.FOUND
