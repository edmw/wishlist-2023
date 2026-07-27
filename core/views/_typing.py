from typing import Any, Callable, Protocol

import django.db.models
from django.http import HttpRequest
from django.http.response import HttpResponseBase

import core.models


class HasRequest(Protocol):
    request: HttpRequest


class HasModel(Protocol):
    model: django.db.models.base.ModelBase


class HasObjectList(Protocol):
    object_list: django.db.models.QuerySet


class SupportsViewSetup(Protocol):
    def setup(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None: ...


class DoesViewDispatching(Protocol):
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseBase: ...


class HasUser(Protocol):
    user: core.models.User | None

    try_user: Callable[[], core.models.User]


class HasWishlist(Protocol):
    wishlist_id: core.models.WishlistID | None = None
    wishlist: core.models.Wishlist | None = None

    try_wishlist: Callable[[], core.models.Wishlist]
