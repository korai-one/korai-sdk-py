"""Tests for korai._errors classes."""

from __future__ import annotations

import httpx
import pytest
import respx

from korai import (
    KoraiAPIError,
    KoraiAuthError,
    KoraiBadRequestError,
    KoraiClient,
    KoraiConfigError,
    KoraiConnectionError,
    KoraiError,
    KoraiNotFoundError,
    KoraiPermissionError,
    KoraiRateLimitError,
    KoraiServerError,
    KoraiUnprocessableError,
    KoraiValidationError,
)


def test_api_error_extracts_message_from_body() -> None:
    err = KoraiAPIError(
        status_code=400,
        body={"error": {"message": "bad", "type": "invalid_request"}},
    )
    assert err.status_code == 400
    assert err.message == "bad"
    assert err.error_type == "invalid_request"
    assert "[400]" in str(err)


def test_api_error_with_string_error_field() -> None:
    err = KoraiAPIError(status_code=403, body={"error": "forbidden"})
    assert err.message == "forbidden"


def test_api_error_with_no_body() -> None:
    err = KoraiAPIError(status_code=500)
    assert err.message == "HTTP 500"


def test_subclass_inheritance() -> None:
    auth_err = KoraiAuthError(status_code=401)
    assert isinstance(auth_err, KoraiAPIError)
    assert isinstance(auth_err, KoraiError)

    nf = KoraiNotFoundError(status_code=404)
    assert isinstance(nf, KoraiAPIError)

    rl = KoraiRateLimitError(status_code=429, retry_after=5.0)
    assert rl.retry_after == 5.0


def test_config_and_validation_are_distinct_subclasses() -> None:
    assert issubclass(KoraiConfigError, KoraiError)
    assert not issubclass(KoraiConfigError, KoraiAPIError)
    assert issubclass(KoraiValidationError, KoraiError)
    assert not issubclass(KoraiValidationError, KoraiAPIError)


def test_can_catch_with_base_exception() -> None:
    with pytest.raises(KoraiError):
        raise KoraiAuthError(status_code=401, message="nope")
    with pytest.raises(KoraiError):
        raise KoraiConfigError("missing db_url")


def test_new_taxonomy_subclass_inheritance() -> None:
    for exc in (
        KoraiBadRequestError(status_code=400),
        KoraiPermissionError(status_code=403),
        KoraiUnprocessableError(status_code=422),
        KoraiServerError(status_code=503),
        KoraiConnectionError(status_code=0),
    ):
        assert isinstance(exc, KoraiAPIError)
        assert isinstance(exc, KoraiError)


def test_request_id_attribute_defaults_none() -> None:
    assert KoraiAPIError(status_code=500).request_id is None
    assert KoraiAPIError(status_code=500, request_id="req-1").request_id == "req-1"


# --- status -> class mapping via the HTTP layer --------------------------


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (400, KoraiBadRequestError),
        (401, KoraiAuthError),
        (403, KoraiPermissionError),
        (404, KoraiNotFoundError),
        (422, KoraiUnprocessableError),
        (429, KoraiRateLimitError),
        (500, KoraiServerError),
        (503, KoraiServerError),
    ],
)
async def test_status_maps_to_class(
    client: KoraiClient,
    respx_mock: respx.Router,
    status: int,
    expected: type[KoraiAPIError],
) -> None:
    respx_mock.get("/map").mock(return_value=httpx.Response(status))
    with pytest.raises(expected) as exc:
        await client._request("GET", "/map")
    assert exc.value.status_code == status
    # 403 must no longer raise the auth error (it has its own class now).
    if status == 403:
        assert not isinstance(exc.value, KoraiAuthError)


async def test_transport_failure_maps_to_connection_error(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.get("/down").mock(side_effect=httpx.ConnectError("refused"))
    with pytest.raises(KoraiConnectionError) as exc:
        await client._request("GET", "/down")
    assert exc.value.status_code == 0


@pytest.mark.parametrize(
    "header_name", ["x-request-id", "request-id", "x-korai-request-id"]
)
async def test_request_id_surfaced_from_header(
    client: KoraiClient, respx_mock: respx.Router, header_name: str
) -> None:
    respx_mock.get("/rid").mock(
        return_value=httpx.Response(500, headers={header_name: "req-abc-123"})
    )
    with pytest.raises(KoraiServerError) as exc:
        await client._request("GET", "/rid")
    assert exc.value.request_id == "req-abc-123"
