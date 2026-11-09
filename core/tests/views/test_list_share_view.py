import re
from http import HTTPStatus
from typing import Any, Generator, cast

import pytest
from django.core import mail
from django.http import HttpResponse
from django.test import Client
from django.urls import reverse

from core import constants
from core.models import Wishlist, WishlistID, WishlistInvitation
from core.models.types import InvitationState, ItemOrdering, Visibility
from core.tests.conftest import CoreFixture

INVITEE_EMAIL = "invitee@example.com"


@pytest.fixture(autouse=True)
def _locmem_email(settings: Any) -> Generator[None, None, None]:
    """Ensures emails are captured in memory instead of being sent."""
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    mail.outbox = []
    yield
    mail.outbox = []


def _private_list(owner: Any) -> Wishlist:
    return Wishlist.objects.create(
        owner=owner,
        name_field="Private list",
        description_field="",
        visibility_field=Visibility.PRIVATE,
        item_ordering_field=ItemOrdering.NAME_ASCENDING,
    )


@pytest.mark.django_db
class TestListShareView:
    def _get_share(self, client: Client, user_id: Any, list_id: WishlistID) -> HttpResponse:
        response = client.get(
            reverse(
                constants.VIEW_LIST_SHARE,
                kwargs={constants.USER_ID_KEY: user_id, constants.LIST_ID_KEY: list_id},
            )
        )
        return cast(HttpResponse, response)

    def _post_share(
        self, client: Client, user_id: Any, list_id: WishlistID, *, follow: bool = False
    ) -> HttpResponse:
        response = client.post(
            reverse(
                constants.VIEW_LIST_SHARE,
                kwargs={constants.USER_ID_KEY: user_id, constants.LIST_ID_KEY: list_id},
            ),
            data={"email": INVITEE_EMAIL},
            follow=follow,
        )
        return cast(HttpResponse, response)

    def _messages(self, response: HttpResponse) -> list[str]:
        return [str(message) for message in response.context["messages"]]  # type: ignore[index]

    def test_share_view_ok(self, core: CoreFixture, client: Client) -> None:
        """Alice sharing her public wish list with an email address."""
        client.force_login(core.user_alice)
        assert self._get_share(client, core.user_alice.id, core.list_alice.id).status_code == HTTPStatus.OK

    def test_share_view_expiry_note(self, core: CoreFixture, client: Client) -> None:
        """The share page shows the expiry duration derived from the setting."""
        client.force_login(core.user_alice)
        response = self._get_share(client, core.user_alice.id, core.list_alice.id)

        content = response.content.decode()
        assert "The invitation expires after 10 days." in content

    def test_share_view_expiry_note_setting(self, core: CoreFixture, client: Client, settings: Any) -> None:
        """A changed expiry setting is reflected in the share page note."""
        settings.WISHLIST_INVITATION_EXPIRES_AFTER = 3 * 24 * 3600

        client.force_login(core.user_alice)
        response = self._get_share(client, core.user_alice.id, core.list_alice.id)

        assert "The invitation expires after 3 days." in response.content.decode()

    def test_share_view_sends_invitation(self, core: CoreFixture, client: Client) -> None:
        """Alice sharing her public wish list creates and sends an invitation."""
        client.force_login(core.user_alice)
        response = self._post_share(client, core.user_alice.id, core.list_alice.id)

        assert response.status_code == HTTPStatus.FOUND
        assert response.headers["Location"] == "/"

        invitation = WishlistInvitation.objects.get()
        assert invitation.wishlist_id == core.list_alice.id
        assert invitation.inviter_id == core.user_alice.id
        assert str(invitation.invitee_email) == INVITEE_EMAIL
        assert invitation.state == InvitationState.PENDING
        assert invitation.sent_at is not None

        assert len(mail.outbox) == 1
        message = mail.outbox[0]
        assert message.to == [INVITEE_EMAIL]
        # The email contains the invitation link with the plaintext token; only its hash is stored.
        match = re.search(r"/invitations/([^/\s]+)/", str(message.body))
        assert match is not None
        assert WishlistInvitation.hash_token(match.group(1)) == str(invitation.code)

    def test_share_view_success_message(self, core: CoreFixture, client: Client) -> None:
        """A success message is shown after sharing a wish list."""
        client.force_login(core.user_alice)
        response = self._post_share(client, core.user_alice.id, core.list_alice.id, follow=True)

        assert "An invitation for sharing your wish list has been successfully sent." in self._messages(
            response
        )

    def test_share_view_invalid_email(self, core: CoreFixture, client: Client) -> None:
        """Posting an invalid email address re-renders the form with errors."""
        client.force_login(core.user_alice)
        response = client.post(
            reverse(
                constants.VIEW_LIST_SHARE,
                kwargs={
                    constants.USER_ID_KEY: core.user_alice.id,
                    constants.LIST_ID_KEY: core.list_alice.id,
                },
            ),
            data={"email": "not-an-email"},
        )

        assert response.status_code == HTTPStatus.OK
        assert WishlistInvitation.objects.count() == 0
        assert len(mail.outbox) == 0

    def test_share_view_private_list_rejected(self, core: CoreFixture, client: Client) -> None:
        """Sharing a private wish list is rejected with an error message."""
        client.force_login(core.user_alice)
        private_list = _private_list(owner=core.user_alice)
        expected_message = (
            "Private wish lists cannot be shared. "
            "Please change the visibility of the list before you share it."
        )

        # The page itself still renders for the owner…
        assert self._get_share(client, core.user_alice.id, private_list.id).status_code == HTTPStatus.OK

        # …but sending an invitation is rejected with an error message.
        response = self._post_share(client, core.user_alice.id, private_list.id, follow=True)
        assert expected_message in self._messages(response)

        assert WishlistInvitation.objects.count() == 0
        assert len(mail.outbox) == 0

    def test_share_view_other_list(self, core: CoreFixture, client: Client) -> None:
        """Bob trying to share alice’s wish list."""
        client.force_login(core.user_bob)
        assert (
            self._get_share(client, core.user_alice.id, core.list_alice.id).status_code
            == HTTPStatus.FORBIDDEN
        )
        assert (
            self._post_share(client, core.user_alice.id, core.list_alice.id).status_code
            == HTTPStatus.FORBIDDEN
        )

    def test_share_view_unauthenticated(self, core: CoreFixture, client: Client) -> None:
        """Anonymous trying to share alice’s wish list."""
        assert (
            self._get_share(client, core.user_alice.id, core.list_alice.id).status_code == HTTPStatus.FOUND
        )
        assert (
            self._post_share(client, core.user_alice.id, core.list_alice.id).status_code == HTTPStatus.FOUND
        )
