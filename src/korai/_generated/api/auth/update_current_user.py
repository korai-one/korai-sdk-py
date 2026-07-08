from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.update_current_user_body import UpdateCurrentUserBody
from ...models.update_current_user_response_200 import UpdateCurrentUserResponse200
from ...types import Response


def _get_kwargs(
    *,
    body: UpdateCurrentUserBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/auth/me",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | UpdateCurrentUserResponse200 | None:
    if response.status_code == 200:
        response_200 = UpdateCurrentUserResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = Error.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = Error.from_dict(response.json())

        return response_401

    if response.status_code == 500:
        response_500 = Error.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Error | UpdateCurrentUserResponse200]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: UpdateCurrentUserBody,
) -> Response[Error | UpdateCurrentUserResponse200]:
    """Update display name and/or password

    Args:
        body (UpdateCurrentUserBody): All fields optional. current_password and new_password must
            be supplied together. display_name is trimmed and clamped to 80 chars.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | UpdateCurrentUserResponse200]
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
    body: UpdateCurrentUserBody,
) -> Error | UpdateCurrentUserResponse200 | None:
    """Update display name and/or password

    Args:
        body (UpdateCurrentUserBody): All fields optional. current_password and new_password must
            be supplied together. display_name is trimmed and clamped to 80 chars.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | UpdateCurrentUserResponse200
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: UpdateCurrentUserBody,
) -> Response[Error | UpdateCurrentUserResponse200]:
    """Update display name and/or password

    Args:
        body (UpdateCurrentUserBody): All fields optional. current_password and new_password must
            be supplied together. display_name is trimmed and clamped to 80 chars.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | UpdateCurrentUserResponse200]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: UpdateCurrentUserBody,
) -> Error | UpdateCurrentUserResponse200 | None:
    """Update display name and/or password

    Args:
        body (UpdateCurrentUserBody): All fields optional. current_password and new_password must
            be supplied together. display_name is trimmed and clamped to 80 chars.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | UpdateCurrentUserResponse200
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
