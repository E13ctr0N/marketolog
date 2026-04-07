"""HTTP client with automatic retry and exponential backoff."""

import asyncio
from typing import Any

import httpx

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


async def fetch_with_retry(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    json: Any = None,
    params: dict[str, Any] | None = None,
    max_retries: int = 3,
    base_delay: float = 1.0,
    timeout: float = 30.0,
) -> httpx.Response:
    """Make an HTTP request with exponential backoff retry on 429/5xx.

    Args:
        url: Request URL.
        method: HTTP method (GET, POST, etc.).
        headers: Optional request headers.
        json: Optional JSON body (for POST/PUT).
        params: Optional query parameters.
        max_retries: Maximum number of attempts (including first).
        base_delay: Initial delay in seconds (doubles each retry).
        timeout: Request timeout in seconds.

    Returns:
        httpx.Response — the last response (success or final failure).
    """
    last_response: httpx.Response | None = None

    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(max_retries):
            last_response = await client.request(
                method,
                url,
                headers=headers,
                json=json,
                params=params,
            )

            if last_response.status_code not in RETRYABLE_STATUS_CODES:
                return last_response

            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)

    return last_response  # type: ignore[return-value]
