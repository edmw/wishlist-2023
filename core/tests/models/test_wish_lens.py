import pytest
from pytest_django import DjangoAssertNumQueries

from core.models import WishLens
from core.models.types.item_ordering import ItemOrdering
from core.tests.conftest import CoreFixture


@pytest.mark.django_db()
def test_lens() -> None:
    lens = WishLens.view()
    wishes = list(lens.queryset.all())
    assert len(wishes) == 4


@pytest.mark.django_db()
def test_lens_reduced_by_archived_wishes(core: CoreFixture) -> None:
    lens = WishLens.view().without_archived()
    lens.without_archived()
    wishes = list(lens.queryset.all())
    assert len(wishes) == 3
    assert core.item_bob_archived not in wishes


@pytest.mark.django_db()
def test_lens_reduced_by_archived_wishes_is_in_illegal_state(core: CoreFixture) -> None:
    lens = WishLens.view().without_archived()
    lens.filter_for_archived = "illegal"  # type: ignore
    with pytest.raises(WishLens.StateError):
        lens.without_archived()


@pytest.mark.django_db()
def test_lens_narrowed_down_to_alices_list(core: CoreFixture) -> None:
    lens = WishLens.view().by_wishlist(list=core.list_alice)
    wishes = list(lens.queryset.all())
    assert len(wishes) == 3
    assert core.item_alice in wishes
    assert core.item_alice_reserved_by_alice in wishes
    assert core.item_alice_reserved_by_bob in wishes


@pytest.mark.django_db()
def test_lens_raises_if_narrowed_down_to_list_twice(core: CoreFixture) -> None:
    lens = WishLens.view().by_wishlist(list=core.list_alice)
    lens.by_wishlist(list=core.list_alice)
    with pytest.raises(WishLens.ViewAlreadyNarrowedDownToListError):
        lens.by_wishlist(list=core.list_bob)


@pytest.mark.django_db()
def test_lens_ordered_by_created_at(core: CoreFixture) -> None:
    lens = WishLens.view().last_created_first()
    wishes = list(lens.queryset.all())
    assert len(wishes) == 4
    assert wishes == [
        core.item_bob_archived,
        core.item_alice_reserved_by_bob,
        core.item_alice_reserved_by_alice,
        core.item_alice,
    ]


@pytest.mark.django_db()
def test_lens_ordered_by_modified_at(core: CoreFixture) -> None:
    lens = WishLens.view().last_modified_first()
    wishes = list(lens.queryset.all())
    assert len(wishes) == 4
    assert wishes == [
        core.item_bob_archived,
        core.item_alice_reserved_by_bob,
        core.item_alice_reserved_by_alice,
        core.item_alice,
    ]


@pytest.mark.django_db()
def test_lens_for_listing(core: CoreFixture, django_assert_num_queries: DjangoAssertNumQueries) -> None:
    lens = WishLens.view().by_wishlist(list=core.list_alice).for_listing()
    wishes = list(lens.queryset.all())
    assert len(wishes) == 3
    # ordered by name
    assert wishes == [core.item_alice_reserved_by_alice, core.item_alice, core.item_alice_reserved_by_bob]
    # lists are prefetched
    with django_assert_num_queries(0):
        _ = wishes[0].wishlist


@pytest.mark.django_db()
def test_lens_for_listing_order_by_name_descending(core: CoreFixture) -> None:
    core.list_alice.item_ordering = ItemOrdering(ItemOrdering.NAME_DESCENDING)
    lens = WishLens.view().by_wishlist(list=core.list_alice).for_listing()
    wishes = list(lens.queryset.all())
    # ordered by name descending
    assert wishes == [core.item_alice_reserved_by_bob, core.item_alice, core.item_alice_reserved_by_alice]
