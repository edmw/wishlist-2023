from http import HTTPMethod, HTTPStatus
from typing import Any, cast
from urllib.parse import quote
from uuid import UUID

import pytest
from django.http import HttpResponse
from django.test import Client
from django.urls import reverse

from core import constants, urls
from core.models import WishlistMembership
from core.models.types import WishlistMembershipRole
from core.services import URLService
from core.tests.conftest import CoreFixture
from core.tests.constants import (
    FAVORITE_ID_ALICE,
    ITEM_ID_ALICE,
    ITEM_ID_ALICE_RESERVED_BY_ALICE,
    LIST_ID_ALICE,
    RESERVATION_ID_ALICE,
    USER_ID_ALICE,
)

KWARGS_USER = {constants.USER_ID_KEY: UUID(USER_ID_ALICE)}
KWARGS_LIST = {**KWARGS_USER, constants.LIST_ID_KEY: UUID(LIST_ID_ALICE)}
KWARGS_ITEM = {**KWARGS_LIST, constants.ITEM_ID_KEY: UUID(ITEM_ID_ALICE)}
KWARGS_ITEM_RESERVED = {**KWARGS_LIST, constants.ITEM_ID_KEY: UUID(ITEM_ID_ALICE_RESERVED_BY_ALICE)}
KWARGS_FAVORITE = {**KWARGS_USER, constants.FAVORITE_ID_KEY: UUID(FAVORITE_ID_ALICE)}
KWARGS_RESERVATION = {**KWARGS_USER, constants.RESERVATION_ID_KEY: UUID(RESERVATION_ID_ALICE)}
KWARGS_MEMBERSHIP = {**KWARGS_LIST, constants.MEMBERSHIP_ID_KEY: UUID(int=0)}
KWARGS_WISHLIST = {constants.LIST_ID_KEY: UUID(LIST_ID_ALICE)}

PARAMS_LIST = {constants.LIST_ID_KEY: [LIST_ID_ALICE]}
PARAMS_ITEM = {constants.ITEM_ID_KEY: [ITEM_ID_ALICE]}

VIEWS_USER = [
    (constants.VIEW_USER_PROFILE, HTTPMethod.GET, KWARGS_USER, None),
    (constants.VIEW_USER_PROFILE_UPDATE, HTTPMethod.GET, KWARGS_USER, None),
    (constants.VIEW_USER_PROFILE_UPDATE, HTTPMethod.POST, KWARGS_USER, None),
    (constants.VIEW_USER_SETTINGS, HTTPMethod.GET, KWARGS_USER, None),
    (constants.VIEW_USER_SETTINGS_UPDATE, HTTPMethod.GET, KWARGS_USER, None),
    (constants.VIEW_USER_SETTINGS_UPDATE, HTTPMethod.POST, KWARGS_USER, None),
    (constants.VIEW_USER_SETTINGS_NOTIFICATION_TEST, HTTPMethod.POST, KWARGS_USER, None),
]
VIEWS_LISTS = [
    (constants.VIEW_LISTS, HTTPMethod.GET, KWARGS_USER, None),
    (constants.VIEW_LIST_CREATE, HTTPMethod.GET, KWARGS_USER, None),
    (constants.VIEW_LIST_CREATE, HTTPMethod.POST, KWARGS_USER, None),
    (constants.VIEW_LIST_UPDATE, HTTPMethod.GET, KWARGS_LIST, None),
    (constants.VIEW_LIST_UPDATE, HTTPMethod.POST, KWARGS_LIST, None),
    (constants.VIEW_LIST_DELETE, HTTPMethod.GET, KWARGS_LIST, None),
    (constants.VIEW_LIST_DELETE, HTTPMethod.POST, KWARGS_LIST, None),
    (constants.VIEW_LIST_EXPORT, HTTPMethod.GET, KWARGS_LIST, None),
]
VIEWS_ITEMS = [
    (constants.VIEW_ITEMS, HTTPMethod.GET, KWARGS_LIST, None),
    (constants.VIEW_ITEM_CREATE, HTTPMethod.GET, KWARGS_LIST, None),
    (constants.VIEW_ITEM_CREATE, HTTPMethod.POST, KWARGS_LIST, None),
    (constants.VIEW_ITEM_UPDATE, HTTPMethod.GET, KWARGS_ITEM, None),
    (constants.VIEW_ITEM_UPDATE, HTTPMethod.POST, KWARGS_ITEM, None),
    (constants.VIEW_ITEM_MANAGE, HTTPMethod.GET, KWARGS_ITEM, None),
    (constants.VIEW_ITEM_MOVE, HTTPMethod.GET, KWARGS_ITEM, None),
    (constants.VIEW_ITEM_MOVE, HTTPMethod.POST, KWARGS_ITEM, None),
    (constants.VIEW_ITEM_ARCHIVE, HTTPMethod.GET, KWARGS_ITEM, None),
    (constants.VIEW_ITEM_ARCHIVE, HTTPMethod.POST, KWARGS_ITEM, None),
    (constants.VIEW_ITEM_UNARCHIVE, HTTPMethod.GET, KWARGS_ITEM, None),
    (constants.VIEW_ITEM_UNARCHIVE, HTTPMethod.POST, KWARGS_ITEM, None),
    (constants.VIEW_ITEM_RELEASE, HTTPMethod.GET, KWARGS_ITEM_RESERVED, None),
    (constants.VIEW_ITEM_RELEASE, HTTPMethod.POST, KWARGS_ITEM_RESERVED, None),
    (constants.VIEW_ITEM_RECEIVE, HTTPMethod.GET, KWARGS_ITEM_RESERVED, None),
    (constants.VIEW_ITEM_RECEIVE, HTTPMethod.POST, KWARGS_ITEM_RESERVED, None),
    (constants.VIEW_ITEM_DELETE, HTTPMethod.GET, KWARGS_ITEM, None),
    (constants.VIEW_ITEM_DELETE, HTTPMethod.POST, KWARGS_ITEM, None),
]
VIEWS_MEMBERSHIPS = [
    (constants.VIEW_MEMBERSHIPS, HTTPMethod.GET, KWARGS_LIST, None),
    (constants.VIEW_MEMBERSHIP_DELETE, HTTPMethod.GET, KWARGS_MEMBERSHIP, None),
    (constants.VIEW_MEMBERSHIP_DELETE, HTTPMethod.POST, KWARGS_MEMBERSHIP, None),
]
VIEWS_FAVORITES = [
    (constants.VIEW_FAVORITES, HTTPMethod.GET, KWARGS_USER, None),
    (constants.VIEW_FAVORITE_CREATE, HTTPMethod.GET, KWARGS_USER, PARAMS_LIST),
    (constants.VIEW_FAVORITE_CREATE, HTTPMethod.POST, KWARGS_USER, PARAMS_LIST),
    (constants.VIEW_FAVORITE_UPDATE, HTTPMethod.GET, KWARGS_FAVORITE, None),
    (constants.VIEW_FAVORITE_UPDATE, HTTPMethod.POST, KWARGS_FAVORITE, None),
    (constants.VIEW_FAVORITE_DELETE, HTTPMethod.GET, KWARGS_FAVORITE, None),
    (constants.VIEW_FAVORITE_DELETE, HTTPMethod.POST, KWARGS_FAVORITE, None),
]
VIEWS_WISHLIST = [
    (constants.VIEW_WISHLIST, HTTPMethod.GET, KWARGS_WISHLIST, None),
]
VIEWS_RESERVATIONS = [
    (constants.VIEW_RESERVATION_CREATE, HTTPMethod.GET, KWARGS_USER, PARAMS_ITEM),
    (constants.VIEW_RESERVATION_CREATE, HTTPMethod.POST, KWARGS_USER, PARAMS_ITEM),
    (constants.VIEW_RESERVATION_UNDO, HTTPMethod.GET, KWARGS_RESERVATION, None),
    (constants.VIEW_RESERVATION_UNDO, HTTPMethod.POST, KWARGS_RESERVATION, None),
]

VIEWS_ALL = (
    VIEWS_USER
    + VIEWS_LISTS
    + VIEWS_ITEMS
    + VIEWS_MEMBERSHIPS
    + VIEWS_FAVORITES
    + VIEWS_WISHLIST
    + VIEWS_RESERVATIONS
)


def _get_response_from_view(
    client: Client,
    view_name: str,
    view_method: str,
    view_kwargs: dict[str, Any],
    view_params: dict[str, list[str]] | None,
) -> tuple[HttpResponse, str]:
    url = reverse(view_name, kwargs=view_kwargs)
    if view_params:
        url = URLService.update_query_parameters(
            url=url,
            parameters=view_params,
        )
    match view_method:
        case HTTPMethod.GET:
            response = client.get(url)
        case HTTPMethod.POST:
            response = client.post(url)
        case _:
            raise ValueError("invalid method")
    return cast(HttpResponse, response), url


def _assert_authorization_required(
    view_name: str,
    view_method: str,
    view_kwargs: dict[str, Any],
    view_params: dict[str, list[str]] | None,
    client: Client,
    views: dict[str, list],
) -> None:
    # without authorization must redirect to login
    response, url = _get_response_from_view(client, view_name, view_method, view_kwargs, view_params)
    assert response.status_code == HTTPStatus.FOUND
    assert response.headers["Location"] == f"/accounts/login/?next={quote(url)}"
    views.setdefault(view_name, []).append(view_method)


@pytest.mark.django_db
def test_authorization_required(core: CoreFixture, client: Client) -> None:
    pages = [page.name for page in urls.pages]

    views = {}
    for name, method, kwargs, params in VIEWS_ALL:
        _assert_authorization_required(name, method, kwargs, params, client, views)

    # all pages must have been tested at least with one method
    assert set(pages) == set(views.keys())


@pytest.mark.parametrize(("view_name", "view_method", "view_kwargs", "view_params"), VIEWS_ALL)
@pytest.mark.django_db
def test_authorization_ok(
    core: CoreFixture,
    view_name: str,
    view_method: str,
    view_kwargs: dict[str, Any],
    view_params: dict[str, list[str]] | None,
    client: Client,
) -> None:
    client.force_login(core.user_alice)

    if view_name == constants.VIEW_MEMBERSHIP_DELETE:
        membership, _ = WishlistMembership.objects.get_or_create(
            wishlist=core.list_alice,
            user=core.user_bob,
            defaults={WishlistMembership.Fields.ROLE: WishlistMembershipRole.EDITOR},
        )
        view_kwargs = {**view_kwargs, constants.MEMBERSHIP_ID_KEY: membership.id}

    response, _ = _get_response_from_view(client, view_name, view_method, view_kwargs, view_params)
    assert response.status_code in [HTTPStatus.OK, HTTPStatus.FOUND]
