"""Restricted IPs module (classic FO API) — API/UI access restriction by source IP.

Covers:
* Restricted IPs List (``/api/2.0/fo/setup/restricted_ips/`` action=list).
* Manage Restricted IPs (``/api/2.0/fo/setup/restricted_ips/``) — activate,
  add, delete, replace, clear.

Managers only. This restricts which IPs may access the user's Qualys account,
not which IPs are scanned.

Docs: Qualys VM/PC API User Guide — "Assets" chapter ("Restricted IPs List",
"Manage Restricted IPs").
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class RestrictedIpsModule(BaseModule):
    """List and manage the subscription's restricted (allowed-source) IP list."""

    module_label = "restricted_ips"

    def register_tools(self, server: FastMCP) -> None:
        self._add_tool(server, self.list_restricted_ips, "list_restricted_ips", tier="read")
        self._add_tool(
            server, self.manage_restricted_ips, "manage_restricted_ips", tier="write"
        )

    def list_restricted_ips(
        self, output_format: str = "xml", echo_request: bool | None = None
    ) -> dict[str, Any]:
        """List the restricted IPs configured for the subscription.

        Args:
            output_format: "xml" (default) or "csv". Qualys only accepts lowercase.
            echo_request: Echo input parameters back in the output.

        Returns:
            Parsed RESTRICTED_IPS_OUTPUT (an <IP_SET> plus enabled/disabled
            <STATUS>), or ``{"raw": ...}`` for CSV.
        """
        params = {
            "action": "list",
            "output_format": output_format.lower(),
            "echo_request": echo_request,
        }
        parse = output_format.lower() == "xml"
        return self._fo(
            "/api/2.0/fo/setup/restricted_ips/", method="GET", params=params, parse=parse
        )

    def manage_restricted_ips(
        self,
        operation: str,
        ips: str | None = None,
        enable: bool | None = None,
        confirm: str | None = None,
        echo_request: bool | None = None,
    ) -> dict[str, Any]:
        """Activate, populate, or clear the restricted IPs list.

        Safety: operations that remove or overwrite the source-IP allow-list
        ("delete", "replace", "clear", and "activate" with enable=False) can lock
        the account out of API/UI access, so they are gated like destructive
        actions — they require the console to run with QUALYS_ENABLE_DESTRUCTIVE
        and the caller to pass ``confirm=<operation>``. The benign operations
        ("add", "activate" with enable=True) proceed as normal writes.

        Args:
            operation: One of:
                "activate" - enable or disable the restricted-IPs feature (use
                    with ``enable``).
                "add" - add IPs to the restricted list (requires ``ips``).
                "delete" - remove IPs from the restricted list (requires ``ips``).
                "replace" - replace the entire restricted list (requires ``ips``).
                "clear" - clear all restricted IPs and disable the feature.
            ips: Comma-separated IPs/ranges/CIDR blocks. Required for "add",
                "delete", and "replace"; ignored otherwise.
            enable: Only used with operation="activate". True to enable the
                restricted-IPs list; False to clear any IPs and disable the feature.
            confirm: Required for gated operations — must equal the ``operation``
                value (e.g. confirm="clear") to proceed.
            echo_request: Echo input parameters back in the output.

        Returns:
            SIMPLE_RETURN confirming the operation (with the resulting STATUS),
            or a confirmation/error dict.
        """
        operation = operation.lower().strip()
        if operation not in ("activate", "add", "delete", "replace", "clear"):
            return {
                "error": "operation must be one of: activate, add, delete, replace, clear"
            }
        # Gate the allow-list-destroying operations behind the destructive flag
        # + explicit confirmation, without hiding the benign add/activate ops.
        disables_access = operation == "activate" and enable is False
        if operation in ("delete", "replace", "clear") or disables_access:
            guard = self._confirm_or_error(confirm, expected=operation)
            if guard:
                return guard
        data = {
            "action": operation,
            "ips": ips,
            "enable": enable,
            "echo_request": echo_request,
        }
        return self._fo("/api/2.0/fo/setup/restricted_ips/", method="POST", data=data)
