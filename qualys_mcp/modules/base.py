"""Base class and shared helpers for all Qualys MCP modules.

Every feature module subclasses :class:`BaseModule`, implements
:meth:`register_tools`, and registers each tool via :meth:`_add_tool` with the
correct safety tier. The base provides:

* Three MCP ``ToolAnnotations`` tiers (read-only / write / destructive).
* **Destructive gating** — destructive tools are only registered when the
  console is started with ``QUALYS_ENABLE_DESTRUCTIVE=true``; even then the
  tool method must call :meth:`_confirm_or_error` to require an explicit
  ``confirm`` argument that matches the target resource.
* Thin wrappers over the three client regimes (``_fo`` / ``_qps`` / ``_gateway``)
  plus response helpers.

Tool naming: every tool is auto-prefixed ``qualys_`` so it reads as
``mcp__qualys-<console>__qualys_<name>`` once the server is namespaced per console.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable

from mcp.server import FastMCP
from mcp.types import ToolAnnotations

from qualys_mcp.client import QualysClient
from qualys_mcp.common.errors import error_dict
from qualys_mcp.common.logging import get_logger

logger = get_logger(__name__)

# Read: never mutates state; safe to call freely.
READ_ONLY_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=True,
)

# Write: creates or updates state, but is not destructive/irreversible.
WRITE_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=False,
    openWorldHint=True,
)

# Destructive: deletes/purges/irreversibly changes state. Gated + needs confirm.
DESTRUCTIVE_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=True,
    idempotentHint=False,
    openWorldHint=True,
)


class BaseModule(ABC):
    """Base class for all Qualys MCP modules."""

    #: Human-friendly module label used in "not entitled" errors.
    module_label: str = "qualys"

    def __init__(self, client: QualysClient):
        self.client = client
        self.tools: list[str] = []
        self.resources: list[str] = []

    # ------------------------------------------------------------------ #
    # Registration API (implemented by subclasses)
    # ------------------------------------------------------------------ #
    @abstractmethod
    def register_tools(self, server: FastMCP) -> None:
        """Register this module's tools with the MCP server."""

    def register_resources(self, server: FastMCP) -> None:
        """Optionally register MCP resources. Default: none."""

    # ------------------------------------------------------------------ #
    # Tool registration + safety gating
    # ------------------------------------------------------------------ #
    def _add_tool(
        self,
        server: FastMCP,
        method: Callable[..., Any],
        name: str,
        tier: str = "read",
    ) -> None:
        """Register a tool with the correct annotations and safety gating.

        Args:
            server: The FastMCP server.
            method: The bound method implementing the tool.
            name: Tool name (without the ``qualys_`` prefix).
            tier: One of ``"read"``, ``"write"``, ``"destructive"``.

        Destructive tools are skipped entirely unless the console was started
        with destructive operations enabled — they simply never appear in the
        tool list, so they cannot be called by accident.
        """
        if tier == "destructive" and not self.client.config.enable_destructive:
            logger.info(
                "Skipping destructive tool 'qualys_%s' (QUALYS_ENABLE_DESTRUCTIVE not set "
                "for console '%s').",
                name,
                self.client.config.console_label,
            )
            return

        annotations = {
            "read": READ_ONLY_ANNOTATIONS,
            "write": WRITE_ANNOTATIONS,
            "destructive": DESTRUCTIVE_ANNOTATIONS,
        }.get(tier, READ_ONLY_ANNOTATIONS)

        prefixed = f"qualys_{name}"
        server.add_tool(method, name=prefixed, annotations=annotations)
        self.tools.append(prefixed)
        logger.debug("Registered tool %s (%s)", prefixed, tier)

    def _confirm_or_error(self, confirm: str | None, expected: str) -> dict[str, Any] | None:
        """Guard the body of a destructive tool.

        Call at the very top of any destructive tool method::

            guard = self._confirm_or_error(confirm, target=asset_id)
            if guard:
                return guard

        Args:
            confirm: The caller-supplied confirmation token.
            expected: The value the caller must echo back (usually the target
                id/name) to prove intent.

        Returns:
            ``None`` when confirmation is valid (proceed); otherwise an error
            dict to return immediately.
        """
        if not self.client.config.enable_destructive:
            return error_dict(
                "Destructive operations are disabled on this console. Restart the "
                "server with QUALYS_ENABLE_DESTRUCTIVE=true to allow them.",
                code="DESTRUCTIVE_DISABLED",
            )
        if confirm is None or str(confirm) != str(expected):
            return error_dict(
                "Destructive action not confirmed. Re-call this tool with "
                f"confirm=\"{expected}\" to proceed. This action is irreversible.",
                code="CONFIRMATION_REQUIRED",
                details={"expected_confirm": expected},
            )
        return None

    # ------------------------------------------------------------------ #
    # Client regime wrappers (thin; keep modules terse and consistent)
    # ------------------------------------------------------------------ #
    def _fo(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """Call a classic FO endpoint. See :meth:`QualysClient.fo`."""
        return self.client.fo(path, **kwargs)

    def _qps(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """Call a QPS REST endpoint. See :meth:`QualysClient.qps`."""
        return self.client.qps(path, **kwargs)

    def _gateway(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """Call a Gateway (JWT) endpoint. See :meth:`QualysClient.gateway`."""
        return self.client.gateway(path, **kwargs)
