from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.chat_completion import ChatCompletion
from ...models.chat_completion_request import ChatCompletionRequest
from ...models.error import Error
from ...types import Response


def _get_kwargs(
    *,
    body: ChatCompletionRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/chat/completions",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ChatCompletion | Error | None:
    if response.status_code == 200:
        response_200 = ChatCompletion.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = Error.from_dict(response.json())

        return response_400

    if response.status_code == 413:
        response_413 = Error.from_dict(response.json())

        return response_413

    if response.status_code == 502:
        response_502 = Error.from_dict(response.json())

        return response_502

    if response.status_code == 503:
        response_503 = Error.from_dict(response.json())

        return response_503

    if response.status_code == 504:
        response_504 = Error.from_dict(response.json())

        return response_504

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ChatCompletion | Error]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: ChatCompletionRequest,
) -> Response[ChatCompletion | Error]:
    """Create a chat completion (buffered or streaming)

     Optional auth: works unauthenticated (rate-limited) or with a JWT/API key. When `stream` is true the
    response is an SSE stream of `chat.completion.chunk` objects terminated by `data: [DONE]`.

    Args:
        body (ChatCompletionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ChatCompletion | Error]
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
    body: ChatCompletionRequest,
) -> ChatCompletion | Error | None:
    """Create a chat completion (buffered or streaming)

     Optional auth: works unauthenticated (rate-limited) or with a JWT/API key. When `stream` is true the
    response is an SSE stream of `chat.completion.chunk` objects terminated by `data: [DONE]`.

    Args:
        body (ChatCompletionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ChatCompletion | Error
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: ChatCompletionRequest,
) -> Response[ChatCompletion | Error]:
    """Create a chat completion (buffered or streaming)

     Optional auth: works unauthenticated (rate-limited) or with a JWT/API key. When `stream` is true the
    response is an SSE stream of `chat.completion.chunk` objects terminated by `data: [DONE]`.

    Args:
        body (ChatCompletionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ChatCompletion | Error]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: ChatCompletionRequest,
) -> ChatCompletion | Error | None:
    """Create a chat completion (buffered or streaming)

     Optional auth: works unauthenticated (rate-limited) or with a JWT/API key. When `stream` is true the
    response is an SSE stream of `chat.completion.chunk` objects terminated by `data: [DONE]`.

    Args:
        body (ChatCompletionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ChatCompletion | Error
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
