import logging
from http import HTTPStatus
from typing import cast

import pytest
from django.http import HttpResponse
from django.test import Client
from django.urls import reverse

from core import constants
from core.models import UserID, WishlistID
from core.services import WishlistCollaborationService
from core.tests._base import AssertLoggingMixin
from core.tests.conftest import CoreFixture


@pytest.mark.django_db
class TestItemsView(AssertLoggingMixin):
    def _get(self, client: Client, user_id: UserID, list_id: WishlistID) -> HttpResponse:
        response = client.get(
            reverse(
                constants.VIEW_ITEMS,
                kwargs={constants.USER_ID_KEY: user_id, constants.LIST_ID_KEY: list_id},
            )
        )
        return cast(HttpResponse, response)

    def test_items_view_ok(self, core: CoreFixture, client: Client) -> None:
        """Alice requesting alice’s wish items."""
        client.force_login(core.user_alice)
        assert self._get(client, core.user_alice.id, core.list_alice.id).status_code == HTTPStatus.OK

    def test_items_view_ok_for_collaborator(self, core: CoreFixture, client: Client) -> None:
        """Bob requesting alice’s wish items as collaborator."""
        client.force_login(core.user_bob)
        WishlistCollaborationService.add_editor(wishlist=core.list_alice, user=core.user_bob)

        assert self._get(client, core.user_alice.id, core.list_alice.id).status_code == HTTPStatus.OK

    def test_items_view_not_allowed(
        self, core: CoreFixture, client: Client, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Bob requesting alice’s wish items without collaboration."""
        client.force_login(core.user_bob)
        assert self._get(client, core.user_alice.id, core.list_alice.id).status_code == HTTPStatus.FORBIDDEN
        self.assert_log_critical(
            caplog,
            "PermissionDenied: Authenticated user requesting list edit without permission.",
        )

    def test_items_view_mismatching_user_and_list_url_logs_warning(
        self, core: CoreFixture, client: Client, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Bob requesting alice's list with bob user id in URL gets not found."""
        client.force_login(core.user_bob)

        response = self._get(client, core.user_bob.id, core.list_alice.id)

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert caplog.records[0].levelno == logging.WARNING
        assert "Inconsistent items URL: user_id does not match list owner." in caplog.records[0].message

    def test_items_view_unauthenticated(self, core: CoreFixture, client: Client) -> None:
        """Anonymous requesting alice’s wish items."""
        assert self._get(client, core.user_alice.id, core.list_alice.id).status_code == HTTPStatus.FOUND
