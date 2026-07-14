"""Small shared utilities for the Qualys MCP server."""

from typing import Any


def clean_params(params: dict[str, Any] | None) -> dict[str, Any]:
    """Drop ``None`` values and normalize booleans/lists for Qualys APIs.

    * ``None`` values are removed (Qualys treats an empty param differently
      from an absent one).
    * ``bool`` -> ``"1"``/``"0"`` (the classic FO API expects 1/0 flags).
    * ``list``/``tuple`` -> comma-joined string (Qualys multi-value params).

    Args:
        params: Raw parameter mapping (or None).

    Returns:
        A cleaned dict safe to pass as query params / form data.
    """
    if not params:
        return {}
    out: dict[str, Any] = {}
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, bool):
            out[key] = "1" if value else "0"
        elif isinstance(value, (list, tuple)):
            joined = ",".join(str(v) for v in value if v is not None)
            if joined:
                out[key] = joined
        else:
            out[key] = value
    return out


def as_list(value: Any) -> list[Any]:
    """Coerce a value that may be a single item or a list into a list.

    xmltodict collapses single-element sequences into a scalar; many Qualys
    list endpoints therefore return either a dict (one item) or a list (many).
    This normalizes both to a list.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def truncate_for_log(text: str, limit: int = 500) -> str:
    """Truncate a long string for safe logging."""
    if len(text) <= limit:
        return text
    return f"{text[:limit]}... [truncated {len(text) - limit} chars]"
