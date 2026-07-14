"""IP Management module (classic FO API) — subscription IP inventory.

Covers:
* IP List (``/api/2.0/fo/asset/ip/`` action=list).
* Add IPs (``/api/2.0/fo/asset/ip/`` action=add).
* Update IPs (``/api/2.0/fo/asset/ip/`` action=update).

Docs: Qualys VM/PC API User Guide — "Assets" chapter ("IP List", "Add IPs",
"Update IPs").
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class IpManagementModule(BaseModule):
    """List, add, and update IP addresses in the Qualys subscription."""

    module_label = "ip_management"

    def register_tools(self, server: FastMCP) -> None:
        self._add_tool(server, self.list_ips, "list_ips", tier="read")
        self._add_tool(server, self.add_ips, "add_ips", tier="write")
        self._add_tool(server, self.update_ips, "update_ips", tier="write")

    def list_ips(
        self,
        ips: str | None = None,
        network_id: str | None = None,
        tracking_method: str | None = None,
        compliance_enabled: bool | None = None,
        certview_enabled: bool | None = None,
        echo_request: bool | None = None,
    ) -> dict[str, Any]:
        """List IP addresses/ranges in the user account.

        Args:
            ips: Comma-separated IPs/ranges to restrict the list to (e.g.
                "10.10.10.44-10.10.10.90"). When omitted, all hosts are listed.
            network_id: Restrict to a custom network ID (Network Support feature
                only; non-Manager users only — Managers always see all networks).
            tracking_method: Restrict to a tracking method: "IP", "DNS", "NETBIOS".
            compliance_enabled: True to list IPs assigned to the Policy Compliance
                module, False for IPs not assigned to it. Combine with
                certview_enabled to scope by module: VM only (False, False), PC
                only (True, False), CertView only (False, True), PC+CertView
                (True, True).
            certview_enabled: True to list IPs assigned to the CertView module,
                False for IPs not assigned to it.
            echo_request: Echo input parameters back in the output.

        Returns:
            Parsed IP_LIST_OUTPUT (an <IP_SET> of <IP>/<IP_RANGE> entries).
        """
        params = {
            "action": "list",
            "ips": ips,
            "network_id": network_id,
            "tracking_method": tracking_method,
            "compliance_enabled": compliance_enabled,
            "certview_enabled": certview_enabled,
            "echo_request": echo_request,
        }
        return self._fo("/api/2.0/fo/asset/ip/", method="GET", params=params)

    def add_ips(
        self,
        ips: str,
        enable_vm: bool = True,
        enable_pc: bool | None = None,
        enable_sca: bool | None = None,
        tracking_method: str | None = None,
        owner: str | None = None,
        ud1: str | None = None,
        ud2: str | None = None,
        ud3: str | None = None,
        comment: str | None = None,
        ag_title: str | None = None,
        enable_certview: bool | None = None,
        echo_request: bool | None = None,
    ) -> dict[str, Any]:
        """Add IP addresses/ranges to the subscription for scanning and reporting.

        You must enable at least one of the VM or PC apps (enable_vm and/or
        enable_pc). CIDR notation is supported for ``ips``.

        Args:
            ips: Comma-separated IPs/ranges to add (e.g. "10.10.30.1-10.10.30.50").
                CIDR notation is supported.
            enable_vm: Add the IPs to the VM module (requires VM enabled for the
                account). Defaults to True.
            enable_pc: Add the IPs to the PC module (requires PC enabled for the account).
            enable_sca: Add the IPs to the SCA module (requires SCA enabled for the account).
            tracking_method: Tracking method to assign: "IP" (default), "DNS", or "NETBIOS".
            owner: Owner login for the new host asset(s) — must be a Manager, or a
                Unit Manager with the "Add assets" permission and sufficient IP quota.
            ud1: Value for user-defined field 1 (max 128 ASCII chars).
            ud2: Value for user-defined field 2 (max 128 ASCII chars).
            ud3: Value for user-defined field 3 (max 128 ASCII chars).
            comment: User-defined comment.
            ag_title: Asset group title to add the host(s) to. Required if the
                caller is a Unit Manager; invalid otherwise.
            enable_certview: Add the IPs to the CertView license.
            echo_request: Echo input parameters back in the output.

        Returns:
            SIMPLE_RETURN confirming the IPs were added, or an error dict.
        """
        data = {
            "action": "add",
            "ips": ips,
            "enable_vm": enable_vm,
            "enable_pc": enable_pc,
            "enable_sca": enable_sca,
            "tracking_method": tracking_method,
            "owner": owner,
            "ud1": ud1,
            "ud2": ud2,
            "ud3": ud3,
            "comment": comment,
            "ag_title": ag_title,
            "enable_certview": enable_certview,
            "echo_request": echo_request,
        }
        return self._fo("/api/2.0/fo/asset/ip/", method="POST", data=data)

    def update_ips(
        self,
        ips: str,
        network_id: str | None = None,
        tracking_method: str | None = None,
        host_dns: str | None = None,
        host_netbios: str | None = None,
        owner: str | None = None,
        ud1: str | None = None,
        ud2: str | None = None,
        ud3: str | None = None,
        comment: str | None = None,
        echo_request: bool | None = None,
    ) -> dict[str, Any]:
        """Update attributes of existing IP addresses in the subscription.

        You cannot change tracking method to/from "EC2" or "AGENT" — those
        updates are silently skipped by Qualys. Duplicate-host conflicts (an IP
        resolved to multiple hostnames across scans) are returned as a
        DUPLICATE_HOSTS_ERROR_OUTPUT and require resolving via the UI.

        Args:
            ips: Comma-separated IPs/ranges to update (e.g. "10.10.10.200,10.10.23.40").
                CIDR notation is supported.
            network_id: Restrict the update to a custom network ID (Network Support
                feature only; default is "0" for the Global Default Network).
            tracking_method: New tracking method: "IP", "DNS", or "NETBIOS".
            host_dns: DNS hostname to match — required with a single IP to
                disambiguate duplicate host entries.
            host_netbios: NetBIOS hostname to match — required with a single IP to
                disambiguate duplicate host entries.
            owner: New owner login (must be a Manager, or another role if the IP
                is already in that user's account).
            ud1: New value for user-defined field 1 (max 128 ASCII chars).
            ud2: New value for user-defined field 2 (max 128 ASCII chars).
            ud3: New value for user-defined field 3 (max 128 ASCII chars).
            comment: New user-defined comment.
            echo_request: Echo input parameters back in the output.

        Returns:
            SIMPLE_RETURN confirming the update, or a DUPLICATE_HOSTS_ERROR_OUTPUT
            / error dict.
        """
        data = {
            "action": "update",
            "ips": ips,
            "network_id": network_id,
            "tracking_method": tracking_method,
            "host_dns": host_dns,
            "host_netbios": host_netbios,
            "owner": owner,
            "ud1": ud1,
            "ud2": ud2,
            "ud3": ud3,
            "comment": comment,
            "echo_request": echo_request,
        }
        return self._fo("/api/2.0/fo/asset/ip/", method="POST", data=data)
