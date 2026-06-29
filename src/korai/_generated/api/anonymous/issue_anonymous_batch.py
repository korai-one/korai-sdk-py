from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.issue_anonymous_batch_body import IssueAnonymousBatchBody
from ...models.token_batch import TokenBatch
from ...types import Response


def _get_kwargs(
    *,
    body: IssueAnonymousBatchBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/anonymous/issue",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | TokenBatch | None:
    if response.status_code == 200:
        response_200 = TokenBatch.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = Error.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = Error.from_dict(response.json())

        return response_401

    if response.status_code == 403:
        response_403 = Error.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = Error.from_dict(response.json())

        return response_404

    if response.status_code == 409:
        response_409 = Error.from_dict(response.json())

        return response_409

    if response.status_code == 503:
        response_503 = Error.from_dict(response.json())

        return response_503

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Error | TokenBatch]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: IssueAnonymousBatchBody,
) -> Response[Error | TokenBatch]:
    """Mint a paid-tier token batch from a Stripe subscription

     Requires the user JWT; cross-checks that the subscription belongs to the caller. One batch per
    (subscription, 4h tranche).

    Args:
        body (IssueAnonymousBatchBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | TokenBatch]
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
    body: IssueAnonymousBatchBody,
) -> Error | TokenBatch | None:
    """Mint a paid-tier token batch from a Stripe subscription

     Requires the user JWT; cross-checks that the subscription belongs to the caller. One batch per
    (subscription, 4h tranche).

    Args:
        body (IssueAnonymousBatchBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | TokenBatch
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: IssueAnonymousBatchBody,
) -> Response[Error | TokenBatch]:
    """Mint a paid-tier token batch from a Stripe subscription

     Requires the user JWT; cross-checks that the subscription belongs to the caller. One batch per
    (subscription, 4h tranche).

    Args:
        body (IssueAnonymousBatchBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | TokenBatch]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: IssueAnonymousBatchBody,
) -> Error | TokenBatch | None:
    """Mint a paid-tier token batch from a Stripe subscription

     Requires the user JWT; cross-checks that the subscription belongs to the caller. One batch per
    (subscription, 4h tranche).

    Args:
        body (IssueAnonymousBatchBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | TokenBatch
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
