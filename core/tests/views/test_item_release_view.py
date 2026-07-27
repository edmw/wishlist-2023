from http import HTTPStatus
from typing import cast

import pytest
from django.http import HttpResponse
from django.test import Client
from django.urls import reverse

from core import constants
from core.services import WishlistCollaborationService
from core.tests._base import AssertLoggingMixin
from core.tests.conftest import CoreFixture


@pytest.mark.django_db
class TestItemReleaseView(AssertLoggingMixin):
    def _url(self, core: CoreFixture, *, item_id: object) -> str:
        return reverse(
            constants.VIEW_ITEM_RELEASE,
            kwargs={
                constants.USER_ID_KEY: core.user_alice.id,
                constants.LIST_ID_KEY: core.list_alice.id,
                constants.ITEM_ID_KEY: item_id,
            },
        )

    def _get(self, client: Client, core: CoreFixture, *, item_id: object) -> HttpResponse:
        response = client.get(self._url(core, item_id=item_id))
        return cast(HttpResponse, response)

    def _post(self, client: Client, core: CoreFixture, *, item_id: object) -> HttpResponse:
        response = client.post(self._url(core, item_id=item_id))
        return cast(HttpResponse, response)

    def test_item_release_view_get_ok_for_list_owner(self, core: CoreFixture, client: Client) -> None:
        client.force_login(core.user_alice)

        response = self._get(client, core, item_id=core.item_alice_reserved_by_bob.id)

        assert response.status_code == HTTPStatus.OK

    def test_item_release_view_post_ok_for_list_owner_deletes_reservation(
        self, core: CoreFixture, client: Client
    ) -> None:
        client.force_login(core.user_alice)
        reservation = core.item_alice_reserved_by_bob.reservation

        response = self._post(client, core, item_id=core.item_alice_reserved_by_bob.id)

        assert response.status_code == HTTPStatus.FOUND
        assert not reservation.__class__.objects.filter(pk=reservation.id).exists()

    def test_item_release_view_post_not_allowed_for_reservation_holder_without_list_access(
        self, core: CoreFixture, client: Client, caplog: pytest.LogCaptureFixture
    ) -> None:
        client.force_login(core.user_bob)

        response = self._post(client, core, item_id=core.item_alice_reserved_by_bob.id)

        assert response.status_code == HTTPStatus.FORBIDDEN
        self.assert_log_critical(
            caplog,
            "PermissionDenied: Authenticated user requesting list edit without permission.",
        )

    def test_item_release_view_post_ok_for_collaborator_with_list_access(
        self, core: CoreFixture, client: Client
    ) -> None:
        WishlistCollaborationService.add_editor(wishlist=core.list_alice, user=core.user_bob)
        client.force_login(core.user_bob)
        reservation = core.item_alice_reserved_by_bob.reservation

        response = self._post(client, core, item_id=core.item_alice_reserved_by_bob.id)

        assert response.status_code == HTTPStatus.FOUND
        assert not reservation.__class__.objects.filter(pk=reservation.id).exists()

    def test_item_release_view_post_returns_bad_request_for_not_reserved_item(
        self, core: CoreFixture, client: Client
    ) -> None:
        client.force_login(core.user_alice)

        response = self._post(client, core, item_id=core.item_alice.id)

        assert response.status_code == HTTPStatus.BAD_REQUEST
