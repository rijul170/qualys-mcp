"""Normalized error handling for the Qualys MCP server.

Qualys reports errors differently per API family:

* **Classic FO** (``/api/2.0/fo/``): HTTP status codes plus an XML body
  ``<SIMPLE_RETURN><RESPONSE><CODE>...</CODE><TEXT>...</TEXT></RESPONSE></SIMPLE_RETURN>``.
  Rate/concurrency limits use HTTP 409 with ``X-RateLimit-*`` / ``X-Concurrency-Limit-*``
  headers.
* **QPS REST** (``/qps/rest/``): ``<ServiceResponse><responseCode>...</responseCode>
  <responseErrorDetails><errorMessage>...</errorMessage></responseErrorDetails></ServiceResponse>``.
* **Gateway (JWT)**: JSON bodies, e.g. ``{"_error": {...}}`` or
  ``{"message": "...", "errorCode": "..."}``.

All three collapse into a single ``{"error": "...", ...}`` dict so tools return a
consistent, model-friendly shape.
"""

from typing import Any

from qualys_mcp.common.logging import get_logger

logger = get_logger(__name__)


class QualysAuthError(RuntimeError):
    """Raised when authentication against a Qualys console fails."""


class QualysAPIError(RuntimeError):
    """Raised for a hard API failure that should abort a tool call."""


def is_error(response: Any) -> bool:
    """Return True if a normalized response represents an error."""
    return isinstance(response, dict) and "error" in response


def error_dict(
    message: str,
    *,
    status_code: int | None = None,
    code: str | int | None = None,
    details: Any = None,
) -> dict[str, Any]:
    """Build a standardized error dict returned by tools.

    Args:
        message: Human-readable error message.
        status_code: HTTP status code, if any.
        code: Qualys-specific response/error code, if any.
        details: Optional extra context (raw payload snippet, hints).

    Returns:
        A dict with an ``error`` key plus any supplied metadata.
    """
    out: dict[str, Any] = {"error": message}
    if status_code is not None:
        out["status_code"] = status_code
    if code is not None:
        out["qualys_code"] = code
    if details is not None:
        out["details"] = details
    return out


def entitlement_hint(module: str) -> dict[str, Any]:
    """Standard error for a module the console is not subscribed to.

    Qualys returns 2xxx/403-style codes when an account lacks a module
    license. Tools surface this rather than crashing so the same codebase
    can serve consoles with different entitlements.
    """
    return error_dict(
        f"This console does not appear to be entitled to the '{module}' module, "
        f"or the API user lacks the required role/permission for it.",
        code="NOT_ENTITLED",
        details={"module": module},
    )
