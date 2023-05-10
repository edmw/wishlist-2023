"""Provides service functions and a context manager for value caching."""
from __future__ import annotations

import dataclasses
import hashlib
from dataclasses import dataclass
from types import TracebackType
from typing import Any, Optional, Type, cast

from django.conf import settings as django_settings
from django.contrib.auth.models import AbstractUser
from django.core.cache import cache


@dataclass
class CachingKey:
    """Represents a caching key:
    name: Name for this caching key. Use something sensible and unique.
    vary: List of arguments which are used to calculate different caching key
        per vary arguments. Use this to create per-user key, for example:
            `vary=[user.id]`.
    """

    name: str
    vary: list[Any] | None

    def __post_init__(self) -> None:
        """Check values after initialization. It's considered a programming
        bug if any of the values is invalid.
        """
        # This is a sanity check while developing which can be safely removed in production.
        assert self.name is not None  # nosec
        assert len(self.name) > 0  # nosec

    def vary_append(self, arg: Any) -> Any:
        """Appends an argument to the list of vary arguments."""
        if self.vary:
            self.vary.append(arg)
        else:
            self.vary = [arg]

    def __str__(self) -> str:
        """Converts this key to a string value usable as cache key."""
        key = f"{self.name}"
        if self.vary:
            hasher = hashlib.sha256()
            for arg in self.vary:
                hasher.update(str(arg).encode())
                hasher.update(b":")
            hasher.update(django_settings.SECRET_KEY.encode())
            key = f"{key}:{hasher.hexdigest()}"
        return key


class CacheTimeoutOmitted:
    """Sentinel value type for omitted timeout values."""


# sentinel value for omitted timeout values
_timeout_omitted = CacheTimeoutOmitted()


CacheTimeout = int | CacheTimeoutOmitted | None


class CachingService:
    """Service class providing a collection of static functions for value caching."""

    @staticmethod
    def get_value(*, key: CachingKey) -> Any | None:
        """Returns the cached value for the specified caching key or None if
        caching key does not exist.

        Arguments:
            key: CachingKey

        Returns:
            Cached value or None
        """
        return cache.get(str(key))

    @staticmethod
    def set_value(*, key: CachingKey, value: Any, timeout: CacheTimeout = _timeout_omitted) -> None:
        """Sets the specified value in the cache for the specified caching key
        and timeout.

        Arguments:
            key: CachingKey
            value: Any
                Any object which can be pickled safely.
            timeout: CacheTimeout
                Timeout in seconds, can be omitted, default is then the cache’s
                default timeout setting. If set to None, cache entry never
                expires.
        """
        if timeout is _timeout_omitted:
            # use default timeout from django settings if no timeout is specified
            timeout_resolved = cache.default_timeout
        else:
            timeout_resolved = cast(int | None, timeout)
        cache.set(str(key), value, timeout_resolved)


class CacheManager:
    """ContextManager which holds the specified caching key and offers methods to
    get and set a value using the default cache for that key.

    key: `CachingKey` or a string value which will be used for creating a `CachingKey`
    vary_on_user: `User` object to be used to vary the cache key on that user. If the
        specified cache key already has a list of vary arguments the specified user
        will be added.
    timeout: Optional timeout in seconds for the value managed by this manager. Defaults
        to the cache’s default timeout specified in Django settings.
    """

    def __init__(
        self,
        *,
        key: CachingKey | str,
        vary_on_user: AbstractUser | None = None,
        timeout: CacheTimeout = _timeout_omitted,
    ):
        """Initializes this context manager with the caching key and timeout."""
        if isinstance(key, str):
            self.key = CachingKey(name=key, vary=None)
        else:
            # because cache keys will be modified by given vary_on parameters,
            # we need to copy the specified cache key
            self.key = dataclasses.replace(key)
        if vary_on_user:
            self.key.vary_append(vary_on_user.pk)
        self.timeout = timeout

    def __enter__(self) -> CacheManager:
        """Enters the context related to this manager."""
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> bool:
        """Exists the context related to this manager."""
        return False  # propagate out of the context

    def set(self, *, value: Any, timeout: CacheTimeout = _timeout_omitted) -> None:
        """Sets the value for the key managed by this manager."""
        if timeout is _timeout_omitted:
            # use timeout given at construction if no timeout is specified
            timeout = self.timeout
        CachingService.set_value(key=self.key, value=value, timeout=timeout)

    def get(self) -> Any:
        """Returns the value for the key managed by this manager."""
        return CachingService.get_value(key=self.key)
