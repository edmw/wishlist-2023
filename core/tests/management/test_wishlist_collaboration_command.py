from io import StringIO

import pytest
from django.core.management import CommandError, call_command

from core.models import Wishlist, WishlistMembership
from core.models.types import Visibility
from core.tests.conftest import CoreFixture


@pytest.mark.django_db
class TestWishlistCollaborationCommand:
    def test_add_editor_by_user_id(self, core: CoreFixture) -> None:
        out = StringIO()

        call_command(
            "wishlist_collaboration",
            "add-editor",
            "--wishlist-id",
            str(core.list_alice.id),
            "--user-id",
            str(core.user_bob.id),
            stdout=out,
        )

        assert WishlistMembership.objects.filter(wishlist=core.list_alice, user=core.user_bob).exists()
        assert "Added editor" in out.getvalue()

    def test_add_editor_by_email_idempotent(self, core: CoreFixture) -> None:
        out = StringIO()

        call_command(
            "wishlist_collaboration",
            "add-editor",
            "--wishlist-id",
            str(core.list_alice.id),
            "--user-email",
            core.user_bob.email,
            stdout=out,
        )
        call_command(
            "wishlist_collaboration",
            "add-editor",
            "--wishlist-id",
            str(core.list_alice.id),
            "--user-email",
            core.user_bob.email,
            stdout=out,
        )

        assert WishlistMembership.objects.filter(wishlist=core.list_alice, user=core.user_bob).count() == 1
        assert "already assigned" in out.getvalue()

    def test_remove_editor_idempotent(self, core: CoreFixture) -> None:
        out = StringIO()

        call_command(
            "wishlist_collaboration",
            "remove-editor",
            "--wishlist-id",
            str(core.list_alice.id),
            "--user-id",
            str(core.user_bob.id),
            stdout=out,
        )
        assert "was not assigned" in out.getvalue()

        call_command(
            "wishlist_collaboration",
            "add-editor",
            "--wishlist-id",
            str(core.list_alice.id),
            "--user-id",
            str(core.user_bob.id),
            stdout=out,
        )
        call_command(
            "wishlist_collaboration",
            "remove-editor",
            "--wishlist-id",
            str(core.list_alice.id),
            "--user-id",
            str(core.user_bob.id),
            stdout=out,
        )

        assert not WishlistMembership.objects.filter(wishlist=core.list_alice, user=core.user_bob).exists()
        assert "Removed editor" in out.getvalue()

    def test_reject_owner_as_editor(self, core: CoreFixture) -> None:
        with pytest.raises(CommandError):
            call_command(
                "wishlist_collaboration",
                "add-editor",
                "--wishlist-id",
                str(core.list_alice.id),
                "--user-id",
                str(core.user_alice.id),
            )

    def test_reject_private_wishlist_editor(self, core: CoreFixture) -> None:
        list_alice = Wishlist.objects.get(pk=core.list_alice.pk)
        list_alice.visibility_field = Visibility.PRIVATE
        list_alice.save(update_fields=[list_alice.Fields.VISIBILITY])

        with pytest.raises(CommandError):
            call_command(
                "wishlist_collaboration",
                "add-editor",
                "--wishlist-id",
                str(list_alice.id),
                "--user-id",
                str(core.user_bob.id),
            )
