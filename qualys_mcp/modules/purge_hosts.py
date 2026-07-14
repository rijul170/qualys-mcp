"""Purge Hosts module (classic FO API) — remove assessment data from hosts.

Covers Purge Hosts (``/api/2.0/fo/asset/host/?action=purge``) — DESTRUCTIVE.

Purging removes vulnerability and/or compliance assessment data associated
with hosts (scan results themselves are not removed, but purged hosts will
not appear in new reports). This does not delete the host asset record itself.

Docs: Qualys VM/PC API User Guide — "Assets" chapter ("Purge Hosts").
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class PurgeHostsModule(BaseModule):
    """Purge vulnerability and/or compliance assessment data from hosts."""

    module_label = "purge_hosts"

    def register_tools(self, server: FastMCP) -> None:
        self._add_tool(server, self.purge_hosts, "purge_hosts", tier="destructive")

    def purge_hosts(
        self,
        ids: str | None = None,
        ips: str | None = None,
        ag_ids: str | None = None,
        ag_titles: str | None = None,
        network_ids: str | None = None,
        data_scope: str | None = None,
        compliance_enabled: bool | None = None,
        no_vm_scan_since: str | None = None,
        no_compliance_scan_since: str | None = None,
        os_pattern: str | None = None,
        echo_request: bool | None = None,
        confirm: str | None = None,
    ) -> dict[str, Any]:
        """Purge assessment data (vulnerability and/or compliance) for hosts. IRREVERSIBLE.

        At least one host-selection parameter must be given: ``ids``, ``ips``,
        ``ag_ids``, or ``ag_titles`` (multiple may be combined). Use
        ``data_scope`` and/or ``compliance_enabled`` to control what gets
        purged — see the Args below for how they interact (whenever
        ``compliance_enabled=True`` is specified, both vulnerability and
        compliance data are purged regardless of ``data_scope``).

        Args:
            ids: Comma-separated host IDs/ranges (e.g. "190-400") to purge.
            ips: Comma-separated IPs/ranges (e.g. "10.10.10.1-10.10.10.100") to purge.
            ag_ids: Comma-separated asset group IDs/ranges identifying hosts to purge.
                Mutually exclusive with ag_titles.
            ag_titles: Comma-separated asset group titles identifying hosts to purge.
                Mutually exclusive with ag_ids.
            network_ids: Comma-separated custom network IDs (Network Support feature
                only) to restrict the purge to.
            data_scope: "vm" to purge vulnerability data only, "pc" to purge
                compliance data only, or "vm,pc" to purge both.
            compliance_enabled: True to purge both vulnerability and compliance
                data (overrides data_scope). False to purge vulnerability data
                only when data_scope is unspecified.
            no_vm_scan_since: Purge hosts not VM-scanned since this date/time
                (YYYY-MM-DD[THH:MM:SSZ], UTC).
            no_compliance_scan_since: Purge hosts not PC-scanned since this date/time.
            os_pattern: PCRE-compliant, URL-encoded regex to match the OS string.
            echo_request: Echo input parameters back in the output.
            confirm: Must equal the literal string ``"PURGE"`` to proceed. There
                is no single target ID for this bulk operation, so a fixed
                sentinel is used to force deliberate confirmation.

        Returns:
            Parsed BATCH_RETURN listing the queued host IDs and the type of
            data queued for purging, or a confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected="PURGE")
        if guard:
            return guard
        if not any([ids, ips, ag_ids, ag_titles]):
            return {
                "error": (
                    "At least one host selection parameter is required: "
                    "ids, ips, ag_ids, or ag_titles."
                )
            }
        data = {
            "action": "purge",
            "ids": ids,
            "ips": ips,
            "ag_ids": ag_ids,
            "ag_titles": ag_titles,
            "network_ids": network_ids,
            "data_scope": data_scope,
            "compliance_enabled": compliance_enabled,
            "no_vm_scan_since": no_vm_scan_since,
            "no_compliance_scan_since": no_compliance_scan_since,
            "os_pattern": os_pattern,
            "echo_request": echo_request,
        }
        return self._fo("/api/2.0/fo/asset/host/", method="POST", data=data)
