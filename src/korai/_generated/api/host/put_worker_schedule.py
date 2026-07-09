from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.put_worker_schedule_body import PutWorkerScheduleBody
from ...models.put_worker_schedule_response_200 import PutWorkerScheduleResponse200
from ...types import Response


def _get_kwargs(
    worker_id: str,
    *,
    body: PutWorkerScheduleBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/host/workers/{worker_id}/schedule".format(
            worker_id=quote(str(worker_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | PutWorkerScheduleResponse200 | None:
    if response.status_code == 200:
        response_200 = PutWorkerScheduleResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = Error.from_dict(response.json())

        return response_400

    if response.status_code == 403:
        response_403 = Error.from_dict(response.json())

        return response_403

    if response.status_code == 503:
        response_503 = Error.from_dict(response.json())

        return response_503

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Error | PutWorkerScheduleResponse200]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    worker_id: str,
    *,
    client: AuthenticatedClient,
    body: PutWorkerScheduleBody,
) -> Response[Error | PutWorkerScheduleResponse200]:
    """Upsert a worker's activity schedule

    Args:
        worker_id (str):
        body (PutWorkerScheduleBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | PutWorkerScheduleResponse200]
    """

    kwargs = _get_kwargs(
        worker_id=worker_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    worker_id: str,
    *,
    client: AuthenticatedClient,
    body: PutWorkerScheduleBody,
) -> Error | PutWorkerScheduleResponse200 | None:
    """Upsert a worker's activity schedule

    Args:
        worker_id (str):
        body (PutWorkerScheduleBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | PutWorkerScheduleResponse200
    """

    return sync_detailed(
        worker_id=worker_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    worker_id: str,
    *,
    client: AuthenticatedClient,
    body: PutWorkerScheduleBody,
) -> Response[Error | PutWorkerScheduleResponse200]:
    """Upsert a worker's activity schedule

    Args:
        worker_id (str):
        body (PutWorkerScheduleBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | PutWorkerScheduleResponse200]
    """

    kwargs = _get_kwargs(
        worker_id=worker_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    worker_id: str,
    *,
    client: AuthenticatedClient,
    body: PutWorkerScheduleBody,
) -> Error | PutWorkerScheduleResponse200 | None:
    """Upsert a worker's activity schedule

    Args:
        worker_id (str):
        body (PutWorkerScheduleBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | PutWorkerScheduleResponse200
    """

    return (
        await asyncio_detailed(
            worker_id=worker_id,
            client=client,
            body=body,
        )
    ).parsed
