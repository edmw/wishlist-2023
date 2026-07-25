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
class TestMembershipsView(AssertLoggingMixin):
    def _get(self, client: Client, user_id: UserID, list_id: WishlistID) -> HttpResponse:
        response = client.get(
            reverse(
                constants.VIEW_MEMBERSHIPS,
                kwargs={constants.USER_ID_KEY: user_id, constants.LIST_ID_KEY: list_id},
            )
        )
        return cast(HttpResponse, response)

    def test_memberships_view_ok_for_owner(self, core: CoreFixture, client: Client) -> None:
        client.force_login(core.user_alice)
        WishlistCollaborationService.add_editor(wishlist=core.list_alice, user=core.user_bob)

        response = self._get(client, core.user_alice.id, core.list_alice.id)

        assert response.status_code == HTTPStatus.OK
        content = response.content.decode("utf-8")
        assert "bob" in content
        assert "editor" in content
        assert "Remove contributor" in content
        assert "/memberships/" in content and "/delete" in content

    def test_memberships_view_empty_state(self, core: CoreFixture, client: Client) -> None:
        client.force_login(core.user_alice)

        response = self._get(client, core.user_alice.id, core.list_alice.id)

        assert response.status_code == HTTPStatus.OK
        assert "This wish list currently has no additional contributors." in response.content.decode(
            "utf-8"
        )

    def test_memberships_view_not_allowed_for_non_owner(
        self, core: CoreFixture, client: Client, caplog: pytest.LogCaptureFixture
    ) -> None:
        client.force_login(core.user_bob)
        WishlistCollaborationService.add_editor(wishlist=core.list_alice, user=core.user_bob)

        response = self._get(client, core.user_alice.id, core.list_alice.id)

        assert response.status_code == HTTPStatus.FORBIDDEN
        self.assert_log_permission_denied_other_user(caplog)

    def test_memberships_view_mismatching_user_and_list_url_logs_warning(
        self, core: CoreFixture, client: Client, caplog: pytest.LogCaptureFixture
    ) -> None:
        client.force_login(core.user_alice)

        response = self._get(client, core.user_alice.id, core.list_bob.id)

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert caplog.records[0].levelno == logging.WARNING
        assert (
            "Inconsistent memberships URL: user_id does not match list owner." in caplog.records[0].message
        )

    def test_memberships_view_unauthenticated(self, core: CoreFixture, client: Client) -> None:
        assert self._get(client, core.user_alice.id, core.list_alice.id).status_code == HTTPStatus.FOUND
