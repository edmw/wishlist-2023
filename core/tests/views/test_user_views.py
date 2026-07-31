from http import HTTPStatus
from typing import cast

import pytest
from django.http import HttpResponse
from django.test import Client
from django.urls import reverse

from core import constants
from core.models import User, UserID, UserSettings
from core.tests._base import AssertLoggingMixin
from core.tests.conftest import CoreFixture


@pytest.mark.django_db
class TestUserProfileView(AssertLoggingMixin):
    def _get(self, client: Client, user_id: UserID) -> HttpResponse:
        response = client.get(
            reverse(
                constants.VIEW_USER_PROFILE,
                kwargs={constants.USER_ID_KEY: user_id},
            )
        )
        return cast(HttpResponse, response)

    def test_profile_view_ok(self, core: CoreFixture, client: Client) -> None:
        """Alice requesting alice’s profile."""
        client.force_login(core.user_alice)
        assert self._get(client, core.user_alice.id).status_code == HTTPStatus.OK

    def test_profile_view_not_allowed(
        self, core: CoreFixture, client: Client, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Bob requesting alice’s profile."""
        client.force_login(core.user_bob)
        assert self._get(client, core.user_alice.id).status_code == HTTPStatus.FORBIDDEN
        self.assert_log_permission_denied_other_user(caplog)

    def test_profile_view_unauthenticated(self, core: CoreFixture, client: Client) -> None:
        """Anonymous requesting alice’s profile."""
        assert self._get(client, core.user_alice.id).status_code == HTTPStatus.FOUND


@pytest.mark.django_db
class TestUserProfileUpdateView(AssertLoggingMixin):
    def _get_update(self, client: Client, user_id: UserID) -> HttpResponse:
        response = client.get(
            reverse(
                constants.VIEW_USER_PROFILE_UPDATE,
                kwargs={constants.USER_ID_KEY: user_id},
            )
        )
        return cast(HttpResponse, response)

    def _post_update(self, client: Client, user_id: UserID) -> HttpResponse:
        response = client.post(
            reverse(
                constants.VIEW_USER_PROFILE_UPDATE,
                kwargs={constants.USER_ID_KEY: user_id},
            ),
            data={
                User.Fields.USERNAME: "aliiiiice",
            },
        )
        return cast(HttpResponse, response)

    def test_profile_update_view_ok(self, core: CoreFixture, client: Client) -> None:
        """Alice updating alice’s profile."""
        client.force_login(core.user_alice)
        assert self._get_update(client, core.user_alice.id).status_code == HTTPStatus.OK
        assert self._post_update(client, core.user_alice.id).status_code == HTTPStatus.FOUND
        assert User.objects.get(pk=core.user_alice.id).username == "aliiiiice"

    def test_profile_update_view_not_allowed(
        self, core: CoreFixture, client: Client, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Bob trying to update alice’s profile."""
        client.force_login(core.user_bob)
        assert self._get_update(client, core.user_alice.id).status_code == HTTPStatus.FORBIDDEN
        self.assert_log_permission_denied_other_user(caplog)
        assert self._post_update(client, core.user_alice.id).status_code == HTTPStatus.FORBIDDEN
        self.assert_log_permission_denied_other_user(caplog)

    def test_profile_update_view_unauthenticated(self, core: CoreFixture, client: Client) -> None:
        """Anonymous trying to update alice’s profile."""
        assert self._get_update(client, core.user_alice.id).status_code == HTTPStatus.FOUND
        assert self._post_update(client, core.user_alice.id).status_code == HTTPStatus.FOUND


@pytest.mark.django_db
class TestUserSettingsView(AssertLoggingMixin):
    def _get(self, client: Client, user_id: UserID) -> HttpResponse:
        response = client.get(
            reverse(
                constants.VIEW_USER_SETTINGS,
                kwargs={constants.USER_ID_KEY: user_id},
            )
        )
        return cast(HttpResponse, response)

    def test_settings_view_ok(self, core: CoreFixture, client: Client) -> None:
        """Alice requesting alice’s profile."""
        client.force_login(core.user_alice)
        assert self._get(client, core.user_alice.id).status_code == HTTPStatus.OK

    def test_settings_view_not_allowed(
        self, core: CoreFixture, client: Client, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Bob requesting alice’s profile."""
        client.force_login(core.user_bob)
        assert self._get(client, core.user_alice.id).status_code == HTTPStatus.FORBIDDEN
        self.assert_log_permission_denied_other_user(caplog)

    def test_settings_view_unauthenticated(self, core: CoreFixture, client: Client) -> None:
        """Anonymous requesting alice’s profile."""
        assert self._get(client, core.user_alice.id).status_code == HTTPStatus.FOUND


@pytest.mark.django_db
class TestUserSettingsUpdateView(AssertLoggingMixin):
    def _get_update(self, client: Client, user_id: UserID) -> HttpResponse:
        response = client.get(
            reverse(
                constants.VIEW_USER_SETTINGS_UPDATE,
                kwargs={constants.USER_ID_KEY: user_id},
            )
        )
        return cast(HttpResponse, response)

    def _post_update(self, client: Client, user_id: UserID) -> HttpResponse:
        response = client.post(
            reverse(
                constants.VIEW_USER_SETTINGS_UPDATE,
                kwargs={constants.USER_ID_KEY: user_id},
            ),
            data={
                UserSettings.Fields.EMAIL_ENABLED: "true",
            },
        )
        return cast(HttpResponse, response)

    def test_settings_update_view_ok(self, core: CoreFixture, client: Client) -> None:
        """Alice updating alice’s settings."""
        client.force_login(core.user_alice)
        assert User.objects.get(pk=core.user_alice.id).settings.email_enabled is False
        assert self._get_update(client, core.user_alice.id).status_code == HTTPStatus.OK
        assert self._post_update(client, core.user_alice.id).status_code == HTTPStatus.FOUND
        assert User.objects.get(pk=core.user_alice.id).settings.email_enabled is True

    def test_settings_update_view_not_allowed(
        self, core: CoreFixture, client: Client, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Bob trying to update alice’s profile."""
        client.force_login(core.user_bob)
        assert self._get_update(client, core.user_alice.id).status_code == HTTPStatus.FORBIDDEN
        self.assert_log_permission_denied_other_user(caplog)
        assert self._post_update(client, core.user_alice.id).status_code == HTTPStatus.FORBIDDEN
        self.assert_log_permission_denied_other_user(caplog)

    def test_settings_update_view_unauthenticated(self, core: CoreFixture, client: Client) -> None:
        """Anonymous trying to update alice’s profile."""
        assert self._get_update(client, core.user_alice.id).status_code == HTTPStatus.FOUND
        assert self._post_update(client, core.user_alice.id).status_code == HTTPStatus.FOUND
