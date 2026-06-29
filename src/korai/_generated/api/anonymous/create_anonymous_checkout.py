from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_anonymous_checkout_body import CreateAnonymousCheckoutBody
from ...models.create_anonymous_checkout_response_200 import CreateAnonymousCheckoutResponse200
from ...models.error import Error
from ...types import Response


def _get_kwargs(
    *,
    body: CreateAnonymousCheckoutBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/anonymous/checkout",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CreateAnonymousCheckoutResponse200 | Error | None:
    if response.status_code == 200:
        response_200 = CreateAnonymousCheckoutResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = Error.from_dict(response.json())

        return response_400

    if response.status_code == 503:
        response_503 = Error.from_dict(response.json())

        return response_503

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[CreateAnonymousCheckoutResponse200 | Error]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: CreateAnonymousCheckoutBody,
) -> Response[CreateAnonymousCheckoutResponse200 | Error]:
    """Start a Stripe Checkout (subscription mode) for an anonymous tier

    Args:
        body (CreateAnonymousCheckoutBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CreateAnonymousCheckoutResponse200 | Error]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    body: CreateAnonymousCheckoutBody,
) -> CreateAnonymousCheckoutResponse200 | Error | None:
    """Start a Stripe Checkout (subscription mode) for an anonymous tier

    Args:
        body (CreateAnonymousCheckoutBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CreateAnonymousCheckoutResponse200 | Error
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: CreateAnonymousCheckoutBody,
) -> Response[CreateAnonymousCheckoutResponse200 | Error]:
    """Start a Stripe Checkout (subscription mode) for an anonymous tier

    Args:
        body (CreateAnonymousCheckoutBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CreateAnonymousCheckoutResponse200 | Error]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: CreateAnonymousCheckoutBody,
) -> CreateAnonymousCheckoutResponse200 | Error | None:
    """Start a Stripe Checkout (subscription mode) for an anonymous tier

    Args:
        body (CreateAnonymousCheckoutBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CreateAnonymousCheckoutResponse200 | Error
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
