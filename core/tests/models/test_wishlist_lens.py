from typing import Iterable, cast

import pytest

from core.models import WishlistLens
from core.models.wishlist_lens import EditableWishlist
from core.services import WishlistCollaborationService
from core.tests.conftest import CoreFixture


@pytest.mark.django_db
def test_lens(core: CoreFixture) -> None:
    lens = WishlistLens.view()
    wishlists = list(lens.qs())
    assert len(wishlists) == 3
    assert core.list_alice in wishlists
    assert core.list_alice_empty in wishlists
    assert core.list_bob in wishlists


@pytest.mark.django_db
def test_lens_narrowed_down_to_owner_alice(core: CoreFixture) -> None:
    lens = WishlistLens.view().by_owner(user=core.user_alice)
    wishlists = list(lens.qs())
    assert len(wishlists) == 2
    assert core.list_alice in wishlists
    assert core.list_alice_empty in wishlists


@pytest.mark.django_db
def test_lens_raises_if_narrowed_down_to_user_twice(core: CoreFixture) -> None:
    lens = WishlistLens.view().by_owner(user=core.user_alice)
    lens.by_owner(user=core.user_alice)
    with pytest.raises(WishlistLens.ViewAlreadyNarrowedDownToOwnerError):
        lens.by_owner(user=core.user_bob)


@pytest.mark.django_db
def test_lens_reduced_by_alice_lists(core: CoreFixture) -> None:
    lens = WishlistLens.view().without_lists(lists=[core.list_alice, core.list_alice_empty])
    wishlists = list(lens.qs())
    assert len(wishlists) == 1
    assert core.list_bob in wishlists


@pytest.mark.django_db
def test_lens_reduced_by_no_lists(core: CoreFixture) -> None:
    lens = WishlistLens.view().without_lists(lists=[])
    wishlists = list(lens.qs())
    assert len(wishlists) == 3


@pytest.mark.django_db
def test_lens_raises_if_reduced_by_lists_twice(core: CoreFixture) -> None:
    lens = WishlistLens.view().without_lists(lists=[core.list_alice, core.list_alice_empty])
    lens.without_lists(lists=[core.list_alice, core.list_alice_empty])
    with pytest.raises(WishlistLens.ViewAlreadyPurgedOfListsError):
        lens.without_lists(lists=[core.list_bob])


@pytest.mark.django_db
def test_lens_ordered_by_name(core: CoreFixture) -> None:
    lens = WishlistLens.view().ordered_by_name()
    wishlists = list(lens.qs())
    assert len(wishlists) == 3
    assert wishlists == [core.list_alice_empty, core.list_alice, core.list_bob]


@pytest.mark.django_db
def test_lens_ordered_by_created_at(core: CoreFixture) -> None:
    lens = WishlistLens.view().last_created_first()
    wishlists = list(lens.qs())
    assert len(wishlists) == 3
    assert wishlists == [core.list_bob, core.list_alice_empty, core.list_alice]


@pytest.mark.django_db
def test_lens_ordered_by_modified_at(core: CoreFixture) -> None:
    lens = WishlistLens.view().last_modified_first()
    wishlists = list(lens.qs())
    assert len(wishlists) == 3
    assert wishlists == [core.list_bob, core.list_alice_empty, core.list_alice]


@pytest.mark.django_db
def test_lens_sorting_order_set_twice() -> None:
    lens = WishlistLens.view().ordered_by_name()
    lens.ordered_by_name()
    with pytest.raises(WishlistLens.ViewAlreadyOrderedError):
        lens.last_modified_first()


@pytest.mark.django_db
def test_lens_counting_wishes(core: CoreFixture) -> None:
    lens = WishlistLens.view().by_owner(user=core.user_alice).last_created_first().counting_wishes()
    lens.counting_wishes()
    wishlists = list(lens.qs())
    assert len(wishlists) == 2
    assert wishlists == [core.list_alice_empty, core.list_alice]
    assert wishlists[0].wishes_count == 0
    assert wishlists[1].wishes_count == 3


@pytest.mark.django_db
def test_lens_not_counting_wishes(core: CoreFixture) -> None:
    lens = WishlistLens.view().by_owner(user=core.user_alice).last_created_first()
    wishlists = list(lens.qs())
    assert len(wishlists) == 2
    with pytest.raises(AttributeError):
        _ = wishlists[0].wishes_count
    with pytest.raises(AttributeError):
        _ = wishlists[1].wishes_count


@pytest.mark.django_db
def test_lens_for_listing(core: CoreFixture) -> None:
    lens = WishlistLens.view().for_listing()
    wishlists = list(lens.qs())
    assert len(wishlists) == 3
    # ordered by name
    assert wishlists == [core.list_alice_empty, core.list_alice, core.list_bob]
    # counting wishes
    assert wishlists[0].wishes_count == 0
    assert wishlists[1].wishes_count == 3
    assert wishlists[2].wishes_count == 1


@pytest.mark.django_db
def test_lens_editable_by_includes_collaboration(core: CoreFixture) -> None:
    WishlistCollaborationService.add_editor(wishlist=core.list_alice, user=core.user_bob)

    lens = WishlistLens.view().editable_by(user=core.user_bob).for_listing()
    wishlists = list(cast(Iterable[EditableWishlist], lens.qs()))

    assert len(wishlists) == 2
    assert [list.name for list in wishlists] == ["Wishes for Alice", "Wishes for Bob"]

    alice_list = [list for list in wishlists if list.id == core.list_alice.id][0]
    bob_list = [list for list in wishlists if list.id == core.list_bob.id][0]

    assert alice_list.is_collaboration is True
    assert bob_list.is_collaboration is False


@pytest.mark.django_db
def test_lens_with_memberships(core: CoreFixture) -> None:
    WishlistCollaborationService.add_editor(wishlist=core.list_alice, user=core.user_bob)
    WishlistCollaborationService.add_editor(wishlist=core.list_alice, user=core.user_carol)

    lens = WishlistLens.view().with_memberships().ordered_by_name()
    wishlists = list(lens.qs())

    assert len(wishlists) == 1
    assert wishlists[0].id == core.list_alice.id


@pytest.mark.django_db
def test_lens_ids(core: CoreFixture) -> None:
    ids = WishlistLens.view().by_owner(user=core.user_alice).ordered_by_name().ids()

    assert ids == [core.list_alice_empty.pk, core.list_alice.pk]
