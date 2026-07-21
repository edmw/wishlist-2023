import pytest
from django.core.exceptions import ValidationError

from core.models import Wishlist, WishlistMembership
from core.models.types import Visibility
from core.services import (
    WishlistCollaborationOwnerAsEditorError,
    WishlistCollaborationPrivateWishlistError,
    WishlistCollaborationService,
)
from core.tests.conftest import CoreFixture


@pytest.mark.django_db
class TestWishlistMembership:
    def test_add_editor_idempotent(self, core: CoreFixture) -> None:
        list_alice = Wishlist.objects.get(pk=core.list_alice.pk)

        created = WishlistCollaborationService.add_editor(wishlist=list_alice, user=core.user_bob)
        created_again = WishlistCollaborationService.add_editor(wishlist=list_alice, user=core.user_bob)

        assert created is True
        assert created_again is False
        assert WishlistMembership.objects.filter(wishlist=list_alice, user=core.user_bob).count() == 1

    def test_remove_editor_idempotent(self, core: CoreFixture) -> None:
        list_alice = Wishlist.objects.get(pk=core.list_alice.pk)

        deleted = WishlistCollaborationService.remove_editor(wishlist=list_alice, user=core.user_bob)
        assert deleted is False

        WishlistCollaborationService.add_editor(wishlist=list_alice, user=core.user_bob)
        deleted = WishlistCollaborationService.remove_editor(wishlist=list_alice, user=core.user_bob)
        deleted_again = WishlistCollaborationService.remove_editor(
            wishlist=list_alice,
            user=core.user_bob,
        )

        assert deleted is True
        assert deleted_again is False

    def test_owner_cannot_be_editor(self, core: CoreFixture) -> None:
        list_alice = Wishlist.objects.get(pk=core.list_alice.pk)

        with pytest.raises(WishlistCollaborationOwnerAsEditorError):
            WishlistCollaborationService.add_editor(wishlist=list_alice, user=core.user_alice)

    def test_private_wishlist_cannot_have_editor(self, core: CoreFixture) -> None:
        list_alice = Wishlist.objects.get(pk=core.list_alice.pk)

        list_alice.visibility_field = Visibility.PRIVATE
        list_alice.save(update_fields=[list_alice.Fields.VISIBILITY])

        with pytest.raises(WishlistCollaborationPrivateWishlistError):
            WishlistCollaborationService.add_editor(wishlist=list_alice, user=core.user_bob)

    def test_visibility_change_to_private_blocked_if_collaborators_exist(self, core: CoreFixture) -> None:
        list_alice = Wishlist.objects.get(pk=core.list_alice.pk)

        WishlistCollaborationService.add_editor(wishlist=list_alice, user=core.user_bob)

        list_alice.visibility_field = Visibility.PRIVATE
        with pytest.raises(ValidationError):
            list_alice.save(update_fields=[list_alice.Fields.VISIBILITY])
