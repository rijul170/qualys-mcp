"""Logging configuration for the Qualys MCP server."""

import logging
import sys

_CONFIGURED = False


def configure_logging(debug: bool = False) -> None:
    """Configure root logging for the server.

    Logs go to stderr so they never corrupt stdio-transport MCP traffic
    (which uses stdout for the JSON-RPC channel).

    Args:
        debug: Enable DEBUG level logging.
    """
    global _CONFIGURED
    level = logging.DEBUG if debug else logging.INFO

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )

    root = logging.getLogger("qualys_mcp")
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    root.propagate = False

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Get a namespaced logger under ``qualys_mcp``.

    Args:
        name: Usually ``__name__`` of the calling module.

    Returns:
        A configured ``logging.Logger``.
    """
    if not _CONFIGURED:
        configure_logging()
    return logging.getLogger(name if name.startswith("qualys_mcp") else f"qualys_mcp.{name}")
