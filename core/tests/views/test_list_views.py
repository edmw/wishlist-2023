from http import HTTPStatus
from typing import cast

import pytest
from django.http import HttpResponse
from django.test import Client
from django.urls import reverse

from core import constants
from core.models import UserID, Wishlist, WishlistID
from core.models.types import ItemOrdering, Visibility
from core.services import WishlistCollaborationService, WishlistService
from core.tests._base import AssertLoggingMixin
from core.tests.conftest import CoreFixture


@pytest.mark.django_db
class TestListCreateView(AssertLoggingMixin):
    def _get_create(self, client: Client, user_id: UserID) -> HttpResponse:
        response = client.get(
            reverse(
                constants.VIEW_LIST_CREATE,
                kwargs={constants.USER_ID_KEY: user_id},
            )
        )
        return cast(HttpResponse, response)

    def _post_create(self, client: Client, user_id: UserID) -> HttpResponse:
        response = client.post(
            reverse(
                constants.VIEW_LIST_CREATE,
                kwargs={constants.USER_ID_KEY: user_id},
            ),
            data={
                Wishlist.Fields.NAME: "A new wish list",
                Wishlist.Fields.VISIBILITY: Visibility.PRIVATE,
                Wishlist.Fields.ITEM_ORDERING: ItemOrdering.NAME_ASCENDING,
            },
        )
        return cast(HttpResponse, response)

    def test_list_create_view_ok(self, core: CoreFixture, client: Client) -> None:
        """Alice creating a wish list for alice’s wish lists."""
        client.force_login(core.user_alice)
        assert self._get_create(client, core.user_alice.id).status_code == HTTPStatus.OK
        assert self._post_create(client, core.user_alice.id).status_code == HTTPStatus.FOUND
        assert Wishlist.objects.get(name_field="A new wish list").owner == core.user_alice

    def test_list_create_view_not_allowed(
        self, core: CoreFixture, client: Client, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Bob trying to create a wish list for alice’s wish lists."""
        client.force_login(core.user_bob)
        assert self._get_create(client, core.user_alice.id).status_code == HTTPStatus.FORBIDDEN
        self.assert_log_permission_denied_other_user(caplog)
        assert self._post_create(client, core.user_alice.id).status_code == HTTPStatus.FORBIDDEN
        self.assert_log_permission_denied_other_user(caplog)

    def test_list_create_view_unauthenticated(self, core: CoreFixture, client: Client) -> None:
        """Anonymous trying to create a wish list for alice’s wish lists."""
        assert self._get_create(client, core.user_alice.id).status_code == HTTPStatus.FOUND
        assert self._post_create(client, core.user_alice.id).status_code == HTTPStatus.FOUND

    def test_list_create_view_limit_uses_total_count(
        self, core: CoreFixture, client: Client, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        client.force_login(core.user_alice)
        monkeypatch.setattr(
            WishlistService,
            "count_wishlists_for_user",
            staticmethod(lambda *, user: Wishlist.MAXIMUM_NUMBER_OF_WISHLISTS_PER_USER),
        )

        assert self._get_create(client, core.user_alice.id).status_code == HTTPStatus.FOUND
        assert Wishlist.objects.filter(name_field="A new wish list").count() == 0


@pytest.mark.django_db
class TestListUpdateView(AssertLoggingMixin):
    def _get_update(self, client: Client, user_id: UserID, list_id: WishlistID) -> HttpResponse:
        response = client.get(
            reverse(
                constants.VIEW_LIST_UPDATE,
                kwargs={constants.USER_ID_KEY: user_id, constants.LIST_ID_KEY: list_id},
            )
        )
        return cast(HttpResponse, response)

    def _post_update(self, client: Client, user_id: UserID, list_id: WishlistID) -> HttpResponse:
        response = client.post(
            reverse(
                constants.VIEW_LIST_UPDATE,
                kwargs={constants.USER_ID_KEY: user_id, constants.LIST_ID_KEY: list_id},
            ),
            data={
                Wishlist.Fields.NAME: "A changed wish list",
                Wishlist.Fields.VISIBILITY: Visibility.PUBLIC,
                Wishlist.Fields.ITEM_ORDERING: ItemOrdering.NAME_DESCENDING,
            },
        )
        return cast(HttpResponse, response)

    def test_list_update_view_ok(self, core: CoreFixture, client: Client) -> None:
        """Alice updating a wish list from alice’s wish lists."""
        client.force_login(core.user_alice)
        user_id = core.user_alice.id
        list_id = core.list_alice.id
        assert self._get_update(client, user_id, list_id).status_code == HTTPStatus.OK
        assert self._post_update(client, user_id, list_id).status_code == HTTPStatus.FOUND
        assert Wishlist.objects.get(pk=list_id).name == "A changed wish list"

    def test_list_update_view_private_visibility_error_rendered_in_form(
        self, core: CoreFixture, client: Client
    ) -> None:
        """Alice reducing visibility on a collaborated list gets a form error."""
        client.force_login(core.user_alice)
        WishlistCollaborationService.add_editor(wishlist=core.list_alice, user=core.user_bob)

        response = client.post(
            reverse(
                constants.VIEW_LIST_UPDATE,
                kwargs={
                    constants.USER_ID_KEY: core.user_alice.id,
                    constants.LIST_ID_KEY: core.list_alice.id,
                },
            ),
            data={
                Wishlist.Fields.NAME: core.list_alice.name,
                Wishlist.Fields.VISIBILITY: Visibility.PRIVATE,
                Wishlist.Fields.ITEM_ORDERING: core.list_alice.item_ordering,
                Wishlist.Fields.MASK_RESERVATIONS: core.list_alice.mask_reservations,
            },
        )

        assert response.status_code == HTTPStatus.OK
        assert response.context["form"].errors[Wishlist.Fields.VISIBILITY] == [
            'Visibility cannot be changed to "Only you" while editors still have access to this list.'
        ]
        assert Wishlist.objects.get(pk=core.list_alice.id).visibility == Visibility.PUBLIC

    def test_list_update_view_other_list(self, core: CoreFixture, client: Client) -> None:
        """Alice updating a wish list from bob’s wish lists."""
        client.force_login(core.user_alice)
        user_id = core.user_alice.id
        list_id = core.list_bob.id
        assert self._get_update(client, user_id, list_id).status_code == HTTPStatus.NOT_FOUND
        assert self._post_update(client, user_id, list_id).status_code == HTTPStatus.NOT_FOUND
        assert Wishlist.objects.get(pk=list_id).name == "Wishes for Bob"

    def test_list_update_view_invalid_list(self, core: CoreFixture, client: Client) -> None:
        """Alice updating a wish list not existing."""
        client.force_login(core.user_alice)
        user_id = core.user_alice.id
        list_id = cast(WishlistID, core.null_id)
        assert self._get_update(client, user_id, list_id).status_code == HTTPStatus.NOT_FOUND
        assert self._post_update(client, user_id, list_id).status_code == HTTPStatus.NOT_FOUND

    def test_list_update_view_not_allowed(
        self, core: CoreFixture, client: Client, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Bob trying to update a wish list from alice’s wish lists."""
        client.force_login(core.user_bob)
        user_id = core.user_alice.id
        list_id = core.list_alice.id
        assert self._get_update(client, user_id, list_id).status_code == HTTPStatus.FORBIDDEN
        self.assert_log_permission_denied_other_user(caplog)
        assert self._post_update(client, user_id, list_id).status_code == HTTPStatus.FORBIDDEN
        self.assert_log_permission_denied_other_user(caplog)

    def test_list_update_view_unauthenticated(self, core: CoreFixture, client: Client) -> None:
        """Anonymous trying to create a wish list for alice’s wish lists."""
        user_id = core.user_alice.id
        list_id = core.list_alice.id
        assert self._get_update(client, user_id, list_id).status_code == HTTPStatus.FOUND
        assert self._post_update(client, user_id, list_id).status_code == HTTPStatus.FOUND


@pytest.mark.django_db
class TestListDeleteView(AssertLoggingMixin):
    def _get_delete(self, client: Client, user_id: UserID, list_id: WishlistID) -> HttpResponse:
        response = client.get(
            reverse(
                constants.VIEW_LIST_DELETE,
                kwargs={constants.USER_ID_KEY: user_id, constants.LIST_ID_KEY: list_id},
            )
        )
        return cast(HttpResponse, response)

    def _post_delete(self, client: Client, user_id: UserID, list_id: WishlistID) -> HttpResponse:
        response = client.post(
            reverse(
                constants.VIEW_LIST_DELETE,
                kwargs={constants.USER_ID_KEY: user_id, constants.LIST_ID_KEY: list_id},
            ),
        )
        return cast(HttpResponse, response)

    def _post_delete_with_confirmation(
        self, client: Client, user_id: UserID, list_id: WishlistID
    ) -> HttpResponse:
        response = client.post(
            reverse(
                constants.VIEW_LIST_DELETE,
                kwargs={constants.USER_ID_KEY: user_id, constants.LIST_ID_KEY: list_id},
            ),
            data={
                "name_confirmation": "Wishes for Alice",
            },
        )
        return cast(HttpResponse, response)

    def test_list_delete_view_ok(self, core: CoreFixture, client: Client) -> None:
        """Alice deleting a wish list from alice’s wish lists."""
        client.force_login(core.user_alice)
        user_id = core.user_alice.id
        list_id = core.list_alice.id
        assert self._get_delete(client, user_id, list_id).status_code == HTTPStatus.OK
        # list has wishes, should not succeed without confirmation
        assert self._post_delete(client, user_id, list_id).status_code == HTTPStatus.OK
        assert Wishlist.objects.filter(pk=list_id).count() == 1
        # list has wishes, should succeed with confirmation
        assert self._post_delete_with_confirmation(client, user_id, list_id).status_code == HTTPStatus.FOUND
        assert Wishlist.objects.filter(pk=list_id).count() == 0
        list_id = core.list_alice_empty.id
        # list has no wishes, should succeed without confirmation
        assert self._post_delete(client, user_id, list_id).status_code == HTTPStatus.FOUND
        assert Wishlist.objects.filter(pk=list_id).count() == 0

    def test_list_delete_view_warns_about_multiple_collaborators_and_wishes(
        self, core: CoreFixture, client: Client
    ) -> None:
        client.force_login(core.user_alice)
        WishlistCollaborationService.add_editor(wishlist=core.list_alice, user=core.user_bob)
        WishlistCollaborationService.add_editor(wishlist=core.list_alice, user=core.user_carol)

        response = self._get_delete(client, core.user_alice.id, core.list_alice.id)
        content = response.content.decode("utf-8")

        assert response.status_code == HTTPStatus.OK
        assert "There are still 3 wishes on your wish list." in content
        assert (
            "This wish list is shared with 2 editors. If you proceed to delete the list, "
            "these editors will lose access to it."
        ) in content
        assert "name_confirmation" in content

    def test_list_delete_view_warns_about_single_collaborator_without_wishes(
        self, core: CoreFixture, client: Client
    ) -> None:
        client.force_login(core.user_alice)
        WishlistCollaborationService.add_editor(wishlist=core.list_alice_empty, user=core.user_bob)

        response = self._get_delete(client, core.user_alice.id, core.list_alice_empty.id)
        content = response.content.decode("utf-8")

        assert response.status_code == HTTPStatus.OK
        assert (
            "This wish list is shared with one editor. If you proceed to delete the list, "
            "this editor will lose access to it."
        ) in content
        assert "name_confirmation" not in content
        assert (
            self._post_delete(client, core.user_alice.id, core.list_alice_empty.id).status_code
            == HTTPStatus.FOUND
        )

    def test_list_delete_view_other_list(self, core: CoreFixture, client: Client) -> None:
        """Alice deleting a wish list from bob’s wish lists."""
        client.force_login(core.user_alice)
        user_id = core.user_alice.id
        list_id = core.list_bob.id
        assert self._get_delete(client, user_id, list_id).status_code == HTTPStatus.NOT_FOUND
        assert self._post_delete(client, user_id, list_id).status_code == HTTPStatus.NOT_FOUND
        assert Wishlist.objects.filter(pk=list_id).count() == 1

    def test_list_delete_view_invalid_list(self, core: CoreFixture, client: Client) -> None:
        """Alice deleting a wish list not existing."""
        client.force_login(core.user_alice)
        user_id = core.user_alice.id
        list_id = cast(WishlistID, core.null_id)
        assert self._get_delete(client, user_id, list_id).status_code == HTTPStatus.NOT_FOUND
        assert self._post_delete(client, user_id, list_id).status_code == HTTPStatus.NOT_FOUND

    def test_list_delete_view_not_allowed(
        self, core: CoreFixture, client: Client, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Bob trying to update a wish list from alice’s wish lists."""
        client.force_login(core.user_bob)
        user_id = core.user_alice.id
        list_id = core.list_alice.id
        assert self._get_delete(client, user_id, list_id).status_code == HTTPStatus.FORBIDDEN
        self.assert_log_permission_denied_other_user(caplog)
        assert self._post_delete(client, user_id, list_id).status_code == HTTPStatus.FORBIDDEN
        self.assert_log_permission_denied_other_user(caplog)

    def test_list_delete_view_unauthenticated(self, core: CoreFixture, client: Client) -> None:
        """Anonymous trying to create a wish list for alice’s wish lists."""
        user_id = core.user_alice.id
        list_id = core.list_alice.id
        assert self._get_delete(client, user_id, list_id).status_code == HTTPStatus.FOUND
        assert self._post_delete(client, user_id, list_id).status_code == HTTPStatus.FOUND
