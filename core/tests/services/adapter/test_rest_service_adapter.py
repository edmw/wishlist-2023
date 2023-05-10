from http import HTTPStatus

import pytest
import requests

from core.services.adapter import RESTServiceError, handle_invalid_response


def test_rest_service_error() -> None:
    with pytest.raises(RESTServiceError) as excinfo:
        raise RESTServiceError(
            status_code=500,
            expected_status_codes=(HTTPStatus.OK,),
        )
    assert (
        str(excinfo.value)
        == "RESTServiceError Status code: 500 Status code (expected): (<HTTPStatus.OK: 200>,)"
    )
    with pytest.raises(RESTServiceError) as excinfo:
        raise RESTServiceError(
            request_url="/",
            status_code=500,
            expected_status_codes=(HTTPStatus.OK,),
        )
    assert (
        str(excinfo.value) == "RESTServiceError Request url: / Status code: 500"
        " Status code (expected): (<HTTPStatus.OK: 200>,)"
    )


def test_rest_service_error_from_error() -> None:
    with pytest.raises(RESTServiceError) as excinfo:
        raise RESTServiceError(
            status_code=500,
            expected_status_codes=(HTTPStatus.OK,),
        ) from KeyError("a")
    assert (
        str(excinfo.value) == "RESTServiceError Status code: 500"
        " Status code (expected): (<HTTPStatus.OK: 200>,) Error: KeyError('a')"
    )


def test_handle_invalid_response_response_is_valid(caplog: pytest.LogCaptureFixture) -> None:
    def valid() -> None:
        return

    handle_invalid_response("response_is_valid_service", RESTServiceError)(valid)()
    assert caplog.records == []


def test_handle_invalid_response_response_raises_keyerror(caplog: pytest.LogCaptureFixture) -> None:
    def invalid() -> None:
        raise KeyError("invalid key")

    with pytest.raises(RESTServiceError):
        handle_invalid_response("raises_keyerror_service", RESTServiceError)(invalid)()
    assert "raises_keyerror_service key error: 'invalid key'" in caplog.text


def test_handle_invalid_response_response_raises_valueerror(caplog: pytest.LogCaptureFixture) -> None:
    def invalid() -> None:
        raise ValueError("invalid value")

    with pytest.raises(RESTServiceError):
        handle_invalid_response("raises_valueerror_service", RESTServiceError)(invalid)()
    assert "raises_valueerror_service value error: invalid value" in caplog.text


def test_handle_invalid_response_response_raises_jsondecodeerror(caplog: pytest.LogCaptureFixture) -> None:
    def invalid() -> None:
        raise requests.exceptions.JSONDecodeError("decode error", "", 0)

    with pytest.raises(RESTServiceError):
        handle_invalid_response("raises_jsondecodeerror_service", RESTServiceError)(invalid)()
    assert "raises_jsondecodeerror_service decode error: decode error" in caplog.text
