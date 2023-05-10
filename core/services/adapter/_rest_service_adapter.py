import functools
import logging
from http import HTTPStatus
from typing import Callable, Container, Iterable, ParamSpec, TypeAlias, TypeVar, Union

import requests
from requests.models import HTTPBasicAuth, Response

logger = logging.getLogger(__name__)


# type for anything which is one or more status code and can be tested with the `in` operator
ExpectedHTTPStatus: TypeAlias = Union[Container[HTTPStatus | int], Iterable[HTTPStatus | int]]


class RESTServiceError(Exception):
    """REST Service error.

    Attributes:
        request_url -- requested url if any
        status_code -- status code from service if any
        expected_status_code -- status codes which were expected if any
        response_text -- text of the response if any
    """

    request_url: str | None
    status_code: int | None
    expected_status_codes: ExpectedHTTPStatus | None
    response_text: str | None

    def __init__(
        self,
        request_url: str | None = None,
        status_code: int | None = None,
        expected_status_codes: ExpectedHTTPStatus | None = None,
        response_text: str | None = None,
    ):
        self.request_url = request_url
        self.status_code = status_code
        self.expected_status_codes = expected_status_codes
        self.response_text = response_text

    def __str__(self) -> str:
        s = f"{self.__class__.__name__}"
        if self.request_url is not None:
            s = s + f" Request url: {self.request_url}"
        if self.status_code is not None:
            s = s + f" Status code: {self.status_code}"
        if self.expected_status_codes is not None:
            s = s + f" Status code (expected): {self.expected_status_codes}"
        if self.response_text is not None:
            response_text = "\\n".join(self.response_text.splitlines())
            s = s + f" Response text: {response_text}"
        if self.__cause__ is not None:
            s = s + f" Error: {self.__cause__.__repr__()}"
        return s


class RESTServiceConnectionError(RESTServiceError):
    """Raised when the REST service is not responding at all."""


class RESTServiceTimeoutError(RESTServiceError):
    """Raised when the REST service is not responding in time."""


class RESTServiceUnavailableError(RESTServiceError):
    """Raised when the REST service is not available. This should be used
    for any unspecific error when accessing the REST service.
    """


class RESTClientError(RESTServiceError):
    """Raised when the REST service there was a client error."""


class RESTService:

    RESTSERVICE_USER = None
    RESTSERVICE_PASSWORD = None
    RESTSERVICE_AUTH = None
    RESTSERVICE_CONNECT_TIMEOUT = 1000
    RESTSERVICE_READ_TIMEOUT = 3000

    @classmethod
    def _request(
        cls,
        url: str,
        method: str = "GET",
        params: dict | None = None,
        json: dict | None = None,
        expected: ExpectedHTTPStatus = (HTTPStatus.OK,),
    ) -> Response:
        if not params:
            params = {}

        try:

            if cls.RESTSERVICE_AUTH:
                auth = cls.RESTSERVICE_AUTH
            else:
                auth = (
                    HTTPBasicAuth(cls.RESTSERVICE_USER, cls.RESTSERVICE_PASSWORD)
                    if cls.RESTSERVICE_USER and cls.RESTSERVICE_PASSWORD
                    else None
                )

            response = requests.request(
                method,
                url,
                params=params,
                json=json,
                auth=auth,
                timeout=(
                    cls.RESTSERVICE_CONNECT_TIMEOUT / 1000,
                    cls.RESTSERVICE_READ_TIMEOUT / 1000,
                ),
            )
            if response.status_code >= 500:
                raise RESTServiceUnavailableError(
                    request_url=url,
                    status_code=response.status_code,
                    expected_status_codes=expected,
                )
            if response.status_code not in expected:
                raise RESTClientError(
                    request_url=url,
                    status_code=response.status_code,
                    expected_status_codes=expected,
                    response_text=response.text,
                )

            return response

        except (
            requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectTimeout,
        ) as timeouterror:
            logger.error("%s timeout error: %r", cls.__name__, timeouterror)
            raise RESTServiceTimeoutError(request_url=url) from timeouterror
        except (requests.exceptions.ConnectionError) as connectionerror:
            logger.error("%s connection error: %r", cls.__name__, connectionerror)
            raise RESTServiceConnectionError(request_url=url) from connectionerror

    @classmethod
    def get(cls, url: str, params: dict | None = None) -> Response:
        """Performs a GET request for the specified url with the given query parameters."""
        return cls._request(url, params=params)

    @classmethod
    def get_or_missing(cls, url: str, params: dict | None = None) -> Response:
        """Performs a GET request for the specified url with the given query parameters.
        Also accepts a 404 Not found for a missing resource.
        """
        return cls._request(url, params=params, expected=(HTTPStatus.OK, HTTPStatus.NOT_FOUND))

    @classmethod
    def post(
        cls,
        url: str,
        json: dict,
        expected: ExpectedHTTPStatus = (HTTPStatus.NO_CONTENT,),
    ) -> Response:
        """Performs a POST request for the specified url with the given json data in the body.
        Expects the resulting status code to be one of the specified status codes.
        """
        return cls._request(url, method="POST", json=json, expected=expected)

    @classmethod
    def patch(
        cls,
        url: str,
        json: dict,
        expected: ExpectedHTTPStatus = (HTTPStatus.NO_CONTENT,),
    ) -> Response:
        """Performs a PATCH request for the specified url with the given json data in the body. Expects
        the resulting status code to be one of the specified status codes.
        """
        return cls._request(url, method="PATCH", json=json, expected=expected)

    @classmethod
    def delete(
        cls,
        url: str,
        expected: ExpectedHTTPStatus = (HTTPStatus.NO_CONTENT,),
    ) -> Response:
        """Performs a DELETE request for the specified url Expects the resulting status code to be
        one of the specified status codes.
        """
        return cls._request(url, method="DELETE", expected=expected)


T = TypeVar("T")
P = ParamSpec("P")


class handle_invalid_response:  # noqa: N801 -- decorators are snake case
    """Decorator to handle common errors when processing REST service JSON responses. This decorator
    catches `JSONDecodeError`, `ValueError`, `KeyError`, then emits a log message of level `error`
    and raises an error of type `service_error`.

    To use this decorator create a function to parse the JSON response into Python data:
    ```
    @handle_invalid_response(service_name='ExampleService', service_error=ExampleServiceInvalidResponse)
    def parse_response(response):
        return <parse response.json() into any python structure>
    return parse_response(response)
    ```
    """

    def __init__(self, service_name: str, service_error: type[RESTServiceError]):
        self.service_name = service_name
        self.service_error = service_error

    def __call__(self, f: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(f)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return f(*args, **kwargs)
            except requests.exceptions.JSONDecodeError as decodeerror:
                logger.error("%s decode error: %s", self.service_name, decodeerror)
                raise self.service_error from decodeerror
            except ValueError as valueerror:
                logger.error("%s value error: %s", self.service_name, valueerror)
                raise self.service_error from valueerror
            except KeyError as keyerror:
                logger.error("%s key error: %s", self.service_name, keyerror)
                raise self.service_error from keyerror

        return wrapped
