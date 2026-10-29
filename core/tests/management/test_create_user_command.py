from io import StringIO

import pytest
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.core.management import CommandError, call_command

from core.models import User


@pytest.mark.django_db
class TestCreateUserCommand:
    def test_create_user_with_verified_email(self) -> None:
        out = StringIO()

        call_command("create_user", "john.doe@example.com", stdout=out)

        user = User.objects.get(email="john.doe@example.com")
        assert user.username == "john.doe"
        assert not user.has_usable_password()

        email_address = EmailAddress.objects.get(user=user, email="john.doe@example.com")
        assert email_address.verified is True
        assert email_address.primary is True

        assert "Created user john.doe@example.com (username 'john.doe')" in out.getvalue()
        assert not SocialAccount.objects.exists()

    def test_create_user_skips_email_verification(self) -> None:
        out = StringIO()

        call_command("create_user", "jane.doe@example.com", "--skip-email-verification", stdout=out)

        user = User.objects.get(email="jane.doe@example.com")
        assert EmailAddress.objects.filter(user=user).count() == 0
        assert "without email verification" in out.getvalue()

    def test_create_user_with_google_id(self) -> None:
        out = StringIO()

        call_command(
            "create_user",
            "john.doe@example.com",
            "--google-id",
            "123456789012345678901",
            stdout=out,
        )

        user = User.objects.get(email="john.doe@example.com")
        account = SocialAccount.objects.get(user=user, provider="google", uid="123456789012345678901")
        assert account.extra_data == {
            "id": "123456789012345678901",
            "email": "john.doe@example.com",
            "verified_email": True,
        }
        assert "Linked Google account" in out.getvalue()

    def test_reject_existing_email(self) -> None:
        User.objects.create_user(username="existing", email="taken@example.com", password=None)

        with pytest.raises(CommandError):
            call_command("create_user", "taken@example.com")

        assert User.objects.filter(email__iexact="taken@example.com").count() == 1

    def test_reject_existing_google_id(self) -> None:
        other = User.objects.create_user(username="other", email="other@example.com", password=None)
        SocialAccount.objects.create(
            user=other, provider="google", uid="123456789012345678901", extra_data={}
        )

        with pytest.raises(CommandError):
            call_command("create_user", "john.doe@example.com", "--google-id", "123456789012345678901")

        assert User.objects.filter(email="john.doe@example.com").count() == 0

    def test_username_collision_gets_suffix(self) -> None:
        User.objects.create_user(username="john.doe", email="existing@example.com", password=None)

        call_command("create_user", "john.doe@example.com")

        user = User.objects.get(email="john.doe@example.com")
        assert user.username == "john.doe2"

    def test_blacklisted_username_gets_suffix(self) -> None:
        call_command("create_user", "admin@example.com")

        user = User.objects.get(email="admin@example.com")
        assert user.username != "admin"
        assert user.username.lower() not in {name.lower() for name in settings.ACCOUNT_USERNAME_BLACKLIST}

    def test_create_user_with_explicit_username(self) -> None:
        out = StringIO()

        call_command("create_user", "john.doe@example.com", "--username", "johndoe42", stdout=out)

        user = User.objects.get(email="john.doe@example.com")
        assert user.username == "johndoe42"
        assert "(username 'johndoe42')" in out.getvalue()

    def test_reject_invalid_username(self) -> None:
        with pytest.raises(CommandError):
            call_command("create_user", "john.doe@example.com", "--username", "has space")

        assert User.objects.filter(email="john.doe@example.com").count() == 0

    def test_reject_blacklisted_username(self) -> None:
        with pytest.raises(CommandError):
            call_command("create_user", "john.doe@example.com", "--username", "admin")

        assert User.objects.filter(email="john.doe@example.com").count() == 0

    def test_reject_taken_username(self) -> None:
        User.objects.create_user(username="johndoe42", email="other@example.com", password=None)

        with pytest.raises(CommandError):
            call_command("create_user", "john.doe@example.com", "--username", "johndoe42")

        assert User.objects.filter(email="john.doe@example.com").count() == 0

    def test_email_without_local_part_falls_back_to_user(self) -> None:
        call_command("create_user", "@example.com")

        user = User.objects.get(email="@example.com")
        assert user.username == "user"
