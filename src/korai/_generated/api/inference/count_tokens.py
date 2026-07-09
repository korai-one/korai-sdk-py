from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.count_tokens_request import CountTokensRequest
from ...models.error import Error
from ...models.token_count import TokenCount
from ...types import Response


def _get_kwargs(
    *,
    body: CountTokensRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/count_tokens",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | TokenCount | None:
    if response.status_code == 200:
        response_200 = TokenCount.from_dict(response.json())

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
) -> Response[Error | TokenCount]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: CountTokensRequest,
) -> Response[Error | TokenCount]:
    """Count prompt tokens accurately (cost preview)

     Returns the exact number of prompt tokens the given messages occupy under the hosting model's own
    tokenizer and chat template — not an estimate. The model alias is resolved the same way as
    `createChatCompletion`, so the count reflects the model that would actually serve the request. This
    performs no billable generation and emits no transparency-log receipt.

    Args:
        body (CountTokensRequest): A strict subset of ChatCompletionRequest — sampling params
            don't affect prompt-token counts, so only model + messages are accepted.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | TokenCount]
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
    body: CountTokensRequest,
) -> Error | TokenCount | None:
    """Count prompt tokens accurately (cost preview)

     Returns the exact number of prompt tokens the given messages occupy under the hosting model's own
    tokenizer and chat template — not an estimate. The model alias is resolved the same way as
    `createChatCompletion`, so the count reflects the model that would actually serve the request. This
    performs no billable generation and emits no transparency-log receipt.

    Args:
        body (CountTokensRequest): A strict subset of ChatCompletionRequest — sampling params
            don't affect prompt-token counts, so only model + messages are accepted.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | TokenCount
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: CountTokensRequest,
) -> Response[Error | TokenCount]:
    """Count prompt tokens accurately (cost preview)

     Returns the exact number of prompt tokens the given messages occupy under the hosting model's own
    tokenizer and chat template — not an estimate. The model alias is resolved the same way as
    `createChatCompletion`, so the count reflects the model that would actually serve the request. This
    performs no billable generation and emits no transparency-log receipt.

    Args:
        body (CountTokensRequest): A strict subset of ChatCompletionRequest — sampling params
            don't affect prompt-token counts, so only model + messages are accepted.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | TokenCount]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: CountTokensRequest,
) -> Error | TokenCount | None:
    """Count prompt tokens accurately (cost preview)

     Returns the exact number of prompt tokens the given messages occupy under the hosting model's own
    tokenizer and chat template — not an estimate. The model alias is resolved the same way as
    `createChatCompletion`, so the count reflects the model that would actually serve the request. This
    performs no billable generation and emits no transparency-log receipt.

    Args:
        body (CountTokensRequest): A strict subset of ChatCompletionRequest — sampling params
            don't affect prompt-token counts, so only model + messages are accepted.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | TokenCount
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
