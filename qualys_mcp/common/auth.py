"""ASGI middleware for HTTP transports.

When the server runs under ``streamable-http`` / ``sse`` (the two-instance
deployment used for the consoles), these wrappers add an optional ``x-api-key``
gate and smooth over a couple of client quirks (trailing slashes, missing
content-type). Mirrors the Falcon MCP HTTP hardening.
"""

from typing import Any, Awaitable, Callable

from qualys_mcp.common.logging import get_logger

logger = get_logger(__name__)

Scope = dict[str, Any]
Receive = Callable[[], Awaitable[dict[str, Any]]]
Send = Callable[[dict[str, Any]], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]


def auth_middleware(app: ASGIApp, api_key: str) -> ASGIApp:
    """Reject HTTP requests lacking a matching ``x-api-key`` header."""

    async def wrapper(scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            headers = dict(scope.get("headers") or [])
            provided = headers.get(b"x-api-key", b"").decode()
            if provided != api_key:
                await send(
                    {
                        "type": "http.response.start",
                        "status": 401,
                        "headers": [(b"content-type", b"application/json")],
                    }
                )
                await send(
                    {
                        "type": "http.response.body",
                        "body": b'{"error":"unauthorized"}',
                    }
                )
                return
        await app(scope, receive, send)

    return wrapper


def strip_trailing_slash_middleware(app: ASGIApp) -> ASGIApp:
    """Normalize ``/mcp/`` -> ``/mcp`` so both forms route correctly."""

    async def wrapper(scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            path = scope.get("path", "")
            if len(path) > 1 and path.endswith("/"):
                scope = {**scope, "path": path.rstrip("/")}
        await app(scope, receive, send)

    return wrapper


def normalize_content_type_middleware(app: ASGIApp) -> ASGIApp:
    """Default missing JSON-RPC POST content-type to ``application/json``."""

    async def wrapper(scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope.get("method") == "POST":
            headers = dict(scope.get("headers") or [])
            if b"content-type" not in headers:
                new_headers = list(scope.get("headers") or [])
                new_headers.append((b"content-type", b"application/json"))
                scope = {**scope, "headers": new_headers}
        await app(scope, receive, send)

    return wrapper
