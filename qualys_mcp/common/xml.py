"""XML <-> dict helpers for the classic FO and QPS REST APIs.

The classic FO API and (by default) the QPS REST API return XML. We normalize
to plain Python dicts with :func:`xmltodict.parse` so tools can return JSON-like
structures. Helpers here also dig out the well-known Qualys envelope shapes.
"""

from typing import Any

import xmltodict

from qualys_mcp.common.logging import get_logger

logger = get_logger(__name__)


def parse_xml(text: str | bytes) -> dict[str, Any]:
    """Parse an XML document into a dict. Returns ``{}`` on empty input."""
    if not text:
        return {}
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="replace")
    try:
        return xmltodict.parse(text) or {}
    except Exception as exc:  # noqa: BLE001 - surface malformed XML as data
        logger.debug("XML parse failed: %s", exc)
        return {"_raw": text if isinstance(text, str) else text.decode("utf-8", "replace")}


def fo_simple_return(parsed: dict[str, Any]) -> dict[str, Any] | None:
    """Extract a classic-FO ``SIMPLE_RETURN`` response, if present.

    Returns a dict like ``{"code": "...", "text": "...", "items": {...}}`` or
    ``None`` when the payload is not a SIMPLE_RETURN envelope.
    """
    sr = parsed.get("SIMPLE_RETURN")
    if not sr:
        return None
    resp = sr.get("RESPONSE", {})
    out: dict[str, Any] = {
        "code": resp.get("CODE"),
        "text": resp.get("TEXT"),
    }
    item_list = resp.get("ITEM_LIST", {}).get("ITEM")
    if item_list is not None:
        out["items"] = item_list
    return out


def qps_service_response(parsed: dict[str, Any]) -> dict[str, Any] | None:
    """Extract a QPS ``ServiceResponse`` envelope, if present.

    Returns ``{"responseCode": "...", "count": N, "data": [...], "error": ...}``
    or ``None`` when not a ServiceResponse.
    """
    sr = parsed.get("ServiceResponse")
    if not sr:
        return None
    out: dict[str, Any] = {
        "responseCode": sr.get("responseCode"),
        "count": sr.get("count"),
        "hasMoreRecords": sr.get("hasMoreRecords"),
        "lastId": sr.get("lastId"),
    }
    if "data" in sr:
        out["data"] = sr.get("data")
    err = sr.get("responseErrorDetails")
    if err:
        out["error"] = err.get("errorMessage")
        out["errorResolution"] = err.get("errorResolution")
    return out
