import httpx
import pytest
import respx

from marketolog.utils.http import fetch_with_retry


@respx.mock
@pytest.mark.asyncio
async def test_fetch_success():
    respx.get("https://api.example.com/data").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    response = await fetch_with_retry("https://api.example.com/data")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


@respx.mock
@pytest.mark.asyncio
async def test_fetch_retry_on_429():
    route = respx.get("https://api.example.com/data")
    route.side_effect = [
        httpx.Response(429, text="Rate limited"),
        httpx.Response(200, json={"ok": True}),
    ]
    response = await fetch_with_retry(
        "https://api.example.com/data", max_retries=3, base_delay=0.01
    )
    assert response.status_code == 200
    assert route.call_count == 2


@respx.mock
@pytest.mark.asyncio
async def test_fetch_retry_on_500():
    route = respx.get("https://api.example.com/data")
    route.side_effect = [
        httpx.Response(500, text="Server Error"),
        httpx.Response(500, text="Server Error"),
        httpx.Response(200, json={"ok": True}),
    ]
    response = await fetch_with_retry(
        "https://api.example.com/data", max_retries=3, base_delay=0.01
    )
    assert response.status_code == 200
    assert route.call_count == 3


@respx.mock
@pytest.mark.asyncio
async def test_fetch_exhausted_retries():
    respx.get("https://api.example.com/data").mock(
        return_value=httpx.Response(429, text="Rate limited")
    )
    response = await fetch_with_retry(
        "https://api.example.com/data", max_retries=2, base_delay=0.01
    )
    assert response.status_code == 429


@respx.mock
@pytest.mark.asyncio
async def test_fetch_no_retry_on_400():
    route = respx.get("https://api.example.com/data")
    route.mock(return_value=httpx.Response(400, text="Bad Request"))
    response = await fetch_with_retry(
        "https://api.example.com/data", max_retries=3, base_delay=0.01
    )
    assert response.status_code == 400
    assert route.call_count == 1


@respx.mock
@pytest.mark.asyncio
async def test_fetch_post_with_headers():
    respx.post("https://api.example.com/data").mock(
        return_value=httpx.Response(200, json={"created": True})
    )
    response = await fetch_with_retry(
        "https://api.example.com/data",
        method="POST",
        headers={"Authorization": "Bearer token123"},
        json={"query": "test"},
    )
    assert response.status_code == 200
    assert response.json() == {"created": True}
