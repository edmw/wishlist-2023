import pytest
from pytest_django import DjangoAssertNumQueries

from core.models import FavoriteLens
from core.tests.conftest import CoreFixture


@pytest.mark.django_db()
def test_lens(core: CoreFixture) -> None:
    lens = FavoriteLens.view()
    favorites = list(lens.queryset.all())
    assert len(favorites) == 2
    assert core.favorite_alice in favorites
    assert core.favorite_bob in favorites


@pytest.mark.django_db()
def test_lens_narrowed_down_to_owner_alice(core: CoreFixture) -> None:
    lens = FavoriteLens.view().by_user(user=core.user_alice)
    favorites = list(lens.queryset.all())
    assert len(favorites) == 1
    assert core.favorite_alice in favorites


@pytest.mark.django_db()
def test_lens_raises_if_narrowed_down_to_user_twice(core: CoreFixture) -> None:
    lens = FavoriteLens.view().by_user(user=core.user_alice)
    lens.by_user(user=core.user_alice)
    with pytest.raises(FavoriteLens.ViewAlreadyNarrowedDownToUserError):
        lens.by_user(user=core.user_bob)


@pytest.mark.django_db()
def test_lens_narrowed_down_to_list_of_alice(core: CoreFixture) -> None:
    lens = FavoriteLens.view().by_wishlist(wishlist=core.list_alice)
    favorites = list(lens.queryset.all())
    assert len(favorites) == 1
    assert core.favorite_alice in favorites


@pytest.mark.django_db()
def test_lens_raises_if_narrowed_down_to_list_twice(core: CoreFixture) -> None:
    lens = FavoriteLens.view().by_wishlist(wishlist=core.list_alice)
    lens.by_wishlist(wishlist=core.list_alice)
    with pytest.raises(FavoriteLens.ViewAlreadyNarrowedDownToListError):
        lens.by_wishlist(wishlist=core.list_bob)


@pytest.mark.django_db()
def test_lens_ordered_by_name(core: CoreFixture) -> None:
    lens = FavoriteLens.view().ordered_by_wishlist_name()
    favorites = list(lens.queryset.all())
    assert len(favorites) == 2
    assert favorites == [core.favorite_bob, core.favorite_alice]


@pytest.mark.django_db()
def test_lens_ordered_by_created_at(core: CoreFixture) -> None:
    lens = FavoriteLens.view().last_created_first()
    favorites = list(lens.queryset.all())
    assert len(favorites) == 2
    assert favorites == [core.favorite_bob, core.favorite_alice]


@pytest.mark.django_db()
def test_lens_ordered_by_modified_at(core: CoreFixture) -> None:
    lens = FavoriteLens.view().last_modified_first()
    favorites = list(lens.queryset.all())
    assert len(favorites) == 2
    assert favorites == [core.favorite_bob, core.favorite_alice]


@pytest.mark.django_db()
def test_lens_sorting_order_set_twice() -> None:
    lens = FavoriteLens.view().ordered_by_wishlist_name()
    lens.ordered_by_wishlist_name()
    with pytest.raises(FavoriteLens.ViewAlreadyOrderedError):
        lens.last_modified_first()


@pytest.mark.django_db()
def test_lens_for_iterating(django_assert_num_queries: DjangoAssertNumQueries) -> None:
    lens = FavoriteLens.view().for_iterating()
    favorites = list(lens.queryset.all())
    assert len(favorites) == 2
    with django_assert_num_queries(0):
        _ = favorites[0].user
    with django_assert_num_queries(0):
        _ = favorites[0].wishlist


@pytest.mark.django_db()
def test_lens_for_listing(core: CoreFixture) -> None:
    lens = FavoriteLens.view().for_listing()
    favorites = list(lens.queryset.all())
    assert len(favorites) == 2
    # ordered by wish list name
    assert favorites == [core.favorite_bob, core.favorite_alice]
    # counting wishes
    assert favorites[0].wishlist.wishes_count == 0
    assert favorites[1].wishlist.wishes_count == 3
