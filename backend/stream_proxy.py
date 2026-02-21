"""
Stream proxy used to bypass browser CORS restrictions for audio streams.
"""

from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

from station_registry import StationRegistry


ICY_HEADERS = {"icy-name", "icy-genre", "icy-br", "icy-metaint", "content-type", "cache-control"}


def _extract_forward_headers(upstream_headers: httpx.Headers) -> dict[str, str]:
    headers: dict[str, str] = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Icy-Metadata",
    }
    for key, value in upstream_headers.items():
        if key.lower() in ICY_HEADERS:
            headers[key] = value
    return headers


def create_router(registry: StationRegistry) -> APIRouter:
    router = APIRouter()

    @router.get("/stream/{station_id}")
    async def proxy_station_stream(
        station_id: str,
        stream_index: int | None = Query(default=None, ge=0),
        retries: int = Query(default=1, ge=0, le=3),
    ):
        station = registry.get_station(station_id)
        if not station:
            raise HTTPException(status_code=404, detail="Station not found")

        stream_candidates = registry.resolve_stream_candidates(station_id, stream_index)
        if not stream_candidates:
            raise HTTPException(status_code=404, detail="No stream URL available")

        last_error: str | None = None
        for candidate in stream_candidates:
            url = candidate.get("url")
            if not isinstance(url, str):
                continue
            if not registry.is_allowed_stream(station_id, url):
                continue

            verify_tls = not bool(candidate.get("allow_insecure_tls", False))
            for _ in range(retries + 1):
                try:
                    client = httpx.AsyncClient(
                        follow_redirects=True,
                        timeout=httpx.Timeout(connect=8.0, read=None, write=10.0, pool=20.0),
                        verify=verify_tls,
                    )
                    request = client.build_request(
                        "GET",
                        url,
                        headers={
                            "User-Agent": "RadioAgnostic/0.7 (+https://radio-agnostic.local)",
                            "Accept": "audio/mpeg,audio/aac,audio/ogg,*/*",
                            "Icy-Metadata": "1",
                        },
                    )
                    upstream = await client.send(request, stream=True)
                    if upstream.status_code != 200:
                        last_error = f"upstream_status_{upstream.status_code}"
                        await upstream.aclose()
                        await client.aclose()
                        continue

                    headers = _extract_forward_headers(upstream.headers)
                    media_type = upstream.headers.get("content-type", "audio/mpeg")
                    return StreamingResponse(
                        upstream.aiter_bytes(chunk_size=16384),
                        media_type=media_type,
                        headers=headers,
                        background=BackgroundTask(_close_upstream, upstream, client),
                    )
                except Exception as exc:  # pragma: no cover
                    last_error = str(exc)
                    continue

        raise HTTPException(status_code=502, detail=f"Stream unavailable: {last_error or 'unknown_error'}")

    @router.get("/health/{station_id}")
    async def check_stream_health(station_id: str):
        station = registry.get_station(station_id)
        if not station:
            raise HTTPException(status_code=404, detail="Station not found")

        results: list[dict[str, Any]] = []
        for idx, stream in enumerate(registry.resolve_stream_candidates(station_id)):
            url = stream.get("url")
            if not isinstance(url, str):
                continue
            verify_tls = not bool(stream.get("allow_insecure_tls", False))
            try:
                async with httpx.AsyncClient(
                    follow_redirects=True,
                    timeout=httpx.Timeout(connect=6.0, read=10.0, write=10.0, pool=20.0),
                    verify=verify_tls,
                ) as client:
                    response = await client.head(url, headers={"User-Agent": "RadioAgnostic/0.7"})
                    results.append(
                        {
                            "stream_index": idx,
                            "healthy": response.status_code == 200,
                            "status": response.status_code,
                            "content_type": response.headers.get("content-type"),
                        }
                    )
            except Exception as exc:  # pragma: no cover
                results.append({"stream_index": idx, "healthy": False, "error": str(exc)})

        return {"station_id": station_id, "streams": results}

    @router.options("/{path:path}")
    async def cors_preflight(path: str):
        return Response(
            content="",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Icy-Metadata",
            },
        )

    return router


async def _close_upstream(upstream: httpx.Response, client: httpx.AsyncClient) -> None:
    await upstream.aclose()
    await client.aclose()
