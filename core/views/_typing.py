from typing import Any, Callable, Protocol

import django.db.models
from django.http import HttpRequest, HttpResponse

import core.models


class HasRequest(Protocol):
    request: HttpRequest


class HasModel(Protocol):
    model: django.db.models.base.ModelBase


class HasObjectList(Protocol):
    object_list: django.db.models.QuerySet


class SupportsViewSetup(Protocol):
    class SetupCallable(Protocol):
        def __call__(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
            ...

    setup: SetupCallable


class DoesViewDispatching(Protocol):
    class DispatchCallable(Protocol):
        def __call__(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
            ...

    dispatch: DispatchCallable


class HasUser(Protocol):
    user: core.models.User | None

    try_user: Callable[[], core.models.User]


class HasWishlist(Protocol):
    wishlist_id: core.models.WishlistID | None = None
    wishlist: core.models.Wishlist | None = None

    try_wishlist: Callable[[], core.models.Wishlist]
