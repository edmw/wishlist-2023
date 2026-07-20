import pytest

from core.models import ReservationLens
from core.tests.conftest import CoreFixture


@pytest.mark.django_db
def test_lens(core: CoreFixture) -> None:
    lens = ReservationLens.view()
    reservations = list(lens.queryset.all())
    assert len(reservations) == 2
    assert core.reservation_alice in reservations
    assert core.reservation_bob in reservations


@pytest.mark.django_db
def test_lens_narrowed_down_to_holder_alice(core: CoreFixture) -> None:
    lens = ReservationLens.view().by_holder(user=core.user_alice)
    reservations = list(lens.queryset.all())
    assert len(reservations) == 1
    assert core.reservation_alice in reservations


@pytest.mark.django_db
def test_lens_raises_if_narrowed_down_to_user_twice(core: CoreFixture) -> None:
    lens = ReservationLens.view().by_holder(user=core.user_alice)
    lens.by_holder(user=core.user_alice)
    with pytest.raises(ReservationLens.ViewAlreadyNarrowedDownToHolderError):
        lens.by_holder(user=core.user_bob)


@pytest.mark.django_db
def test_lens_ordered_by_name(core: CoreFixture) -> None:
    lens = ReservationLens.view().ordered_by_wish_name()
    reservations = list(lens.queryset.all())
    assert len(reservations) == 2
    assert reservations == [core.reservation_alice, core.reservation_bob]


@pytest.mark.django_db
def test_lens_ordered_by_created_at(core: CoreFixture) -> None:
    lens = ReservationLens.view().last_created_first()
    reservations = list(lens.queryset.all())
    assert len(reservations) == 2
    assert reservations == [core.reservation_bob, core.reservation_alice]


@pytest.mark.django_db
def test_lens_ordered_by_modified_at(core: CoreFixture) -> None:
    lens = ReservationLens.view().last_modified_first()
    reservations = list(lens.queryset.all())
    assert len(reservations) == 2
    assert reservations == [core.reservation_bob, core.reservation_alice]


@pytest.mark.django_db
def test_lens_sorting_order_set_twice() -> None:
    lens = ReservationLens.view().ordered_by_wish_name()
    lens.ordered_by_wish_name()
    with pytest.raises(ReservationLens.ViewAlreadyOrderedError):
        lens.last_modified_first()
