import pytest

from core.models import WishlistMembershipLens
from core.services import WishlistCollaborationService
from core.tests.conftest import CoreFixture


@pytest.mark.django_db
def test_lens(core: CoreFixture) -> None:
    lens = WishlistMembershipLens.view()
    memberships = list(lens.qs())

    assert memberships == []


@pytest.mark.django_db
def test_lens_narrowed_down_to_wishlist(core: CoreFixture) -> None:
    WishlistCollaborationService.add_editor(wishlist=core.list_alice, user=core.user_bob)
    WishlistCollaborationService.add_editor(wishlist=core.list_bob, user=core.user_alice)

    lens = WishlistMembershipLens.view().by_wishlist(wishlist=core.list_alice)
    memberships = list(lens.qs())

    assert len(memberships) == 1
    assert memberships[0].wishlist_id == core.list_alice.id
    assert memberships[0].user_id == core.user_bob.id


@pytest.mark.django_db
def test_lens_narrowed_down_to_user(core: CoreFixture) -> None:
    WishlistCollaborationService.add_editor(wishlist=core.list_alice, user=core.user_bob)
    WishlistCollaborationService.add_editor(wishlist=core.list_alice_empty, user=core.user_bob)
    WishlistCollaborationService.add_editor(wishlist=core.list_bob, user=core.user_alice)

    lens = WishlistMembershipLens.view().by_user(user=core.user_bob)
    memberships = list(lens.qs())

    assert len(memberships) == 2
    assert sorted(membership.wishlist_id for membership in memberships) == sorted(
        [core.list_alice.id, core.list_alice_empty.id]
    )


@pytest.mark.django_db
def test_lens_editors_only(core: CoreFixture) -> None:
    WishlistCollaborationService.add_editor(wishlist=core.list_alice, user=core.user_bob)

    lens = WishlistMembershipLens.view().editors_only()
    memberships = list(lens.qs())

    assert len(memberships) == 1
    assert memberships[0].wishlist_id == core.list_alice.id
    assert memberships[0].user_id == core.user_bob.id


@pytest.mark.django_db
def test_lens_for_listing(core: CoreFixture) -> None:
    WishlistCollaborationService.add_editor(wishlist=core.list_alice, user=core.user_bob)
    WishlistCollaborationService.add_editor(wishlist=core.list_alice, user=core.user_carol)

    memberships = list(
        WishlistMembershipLens.view().by_wishlist(wishlist=core.list_alice).for_listing().qs()
    )

    assert len(memberships) == 2
    assert [membership.user_id for membership in memberships] == [core.user_bob.id, core.user_carol.id]


@pytest.mark.django_db
def test_lens_raises_if_narrowed_down_to_other_wishlist(core: CoreFixture) -> None:
    lens = WishlistMembershipLens.view().by_wishlist(wishlist=core.list_alice)
    lens.by_wishlist(wishlist=core.list_alice)

    with pytest.raises(WishlistMembershipLens.ViewAlreadyNarrowedDownToWishlistError):
        lens.by_wishlist(wishlist=core.list_bob)


@pytest.mark.django_db
def test_lens_raises_if_narrowed_down_to_other_user(core: CoreFixture) -> None:
    lens = WishlistMembershipLens.view().by_user(user=core.user_bob)
    lens.by_user(user=core.user_bob)

    with pytest.raises(WishlistMembershipLens.ViewAlreadyNarrowedDownToUserError):
        lens.by_user(user=core.user_carol)
