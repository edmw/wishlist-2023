from __future__ import annotations

import logging
import threading
from http import HTTPStatus
from typing import Any, Protocol

import requests
from requests.auth import AuthBase

logger = logging.getLogger(__name__)


class AuthSupportsRetry(Protocol):
    """Protocol which must be implemented by an auth class if the class is to be
    used with automatic auth retry (see RetryAuth below)."""

    def reset(self) -> None: ...

    def __call__(self, request: requests.PreparedRequest) -> requests.PreparedRequest: ...


class RetryAuth(AuthBase):
    """Auth class which will retry a request if a first try does not succeed
    with an unauthorized response. Can be used with Auth classes which store
    some kind of auth information (cookies, tokens, ...) where this information
    can expire.
    """

    def __init__(self, *, auth: AuthSupportsRetry):
        self.auth = auth
        # keep state in per-thread local storage
        self._thread_local = threading.local()

    def _init_per_thread_state(self) -> None:
        if not hasattr(self._thread_local, "init"):
            self._thread_local.auth_use_attempts = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RetryAuth):
            return NotImplemented
        return self.auth == other.auth

    def _retry_unauthorized(self, response: requests.Response, **kwargs: Any) -> requests.Response | None:
        if response.status_code == HTTPStatus.UNAUTHORIZED:
            # request authorization failed, if this was the first try, authorize again and retry
            if self._thread_local.authtoken_use_attempts < 2:
                self._thread_local.authtoken_use_attempts += 1

                # consume content and release the original connection
                # to allow our new request to reuse the same one
                _ = response.content
                response.close()

                # retry request and return new response

                retry_request = response.request.copy()

                # authorize request
                self.auth.reset()
                self.auth(retry_request)

                if retry_connection := getattr(response, "connection", None):
                    retry_response = retry_connection.send(retry_request, **kwargs)
                    retry_response.history.append(response)
                    retry_response.request = retry_request
                else:
                    logger.critical(
                        f"Connection attribute of response {response!r} "
                        f"for request {response.request!r} missing!"
                    )
                    raise RuntimeError(
                        "Authorization cannot be retried because there is no connection attribute."
                    )

                return retry_response

        else:
            self._thread_local.authtoken_use_attempts = 1
            return response

    def __call__(self, request: requests.PreparedRequest) -> requests.PreparedRequest:
        self._init_per_thread_state()

        # authorize request (this may use some store auth information)
        self.auth(request)

        # hook which will handle a retry for expired auth information
        request.register_hook("response", self._retry_unauthorized)

        # this is the first attempt for this request with this auth information
        self._thread_local.authtoken_use_attempts = 1

        return request


class CookieAuth(AuthBase, AuthSupportsRetry):
    """Implementation of Cookie-based authentication with login.

    1. Call specified login url with specified auth method
    2. Extract Cookies from response
    3. Add Cookies to API requests

    Of course, it is not necessary to login before each single API request.
    Therefore this implementation stores the Cookies once logged in thread
    local storage.

    This could be further improved if the Cookies would be stored in the
    cache, so they would be accessible from different threads.

    NOTE: Because the Cookies will be used only in a per thread manner currently,
    there is no logic to handle expired Cookies.

    IMPORTANT NOTE: Because of the inner workings of requests a prepared request
    may **not** have any Cookies set already.
    """

    def __init__(self, *, get_cookies_url: str, get_cookies_auth: AuthBase):
        self.get_cookies_url = get_cookies_url
        self.get_cookies_auth = get_cookies_auth
        # keep state in per-thread local storage
        self._thread_local = threading.local()

    def _init_per_thread_state(self) -> None:
        if not hasattr(self._thread_local, "init"):
            self._thread_local.init = True
            self._thread_local.cookies = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CookieAuth):
            return NotImplemented
        return all(
            [
                self.get_cookies_url == other.get_cookies_url,
                self.get_cookies_auth == other.get_cookies_auth,
            ]
        )

    def __call__(self, request: requests.PreparedRequest) -> requests.PreparedRequest:
        self._init_per_thread_state()

        if not self._thread_local.cookies:
            s = requests.Session()
            # make login request using auth
            s.get(self.get_cookies_url, auth=self.get_cookies_auth)
            # store cookies
            self._thread_local.cookies = s.cookies

        # add cookies to request
        request.prepare_cookies(self._thread_local.cookies)

        return request

    def reset(self) -> None:
        # enforce re-auth
        self._thread_local.cookies = None
