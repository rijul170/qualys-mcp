"""Virtual Hosts module (classic FO API) — virtual host (FQDN-per-port) configs.

Covers:
* Virtual Host List (``/api/2.0/fo/asset/vhost/`` action=list).
* Manage Virtual Hosts — create/update/add_fqdn/delete_fqdn (action variants).
* Delete Virtual Host (action=delete) — DESTRUCTIVE.

A subscription can have a maximum of 5000 virtual hosts. Total FQDN bytes
(including commas) must stay under 4000 per virtual host.

Docs: Qualys VM/PC API User Guide — "Assets" chapter ("Virtual Host List",
"Manage Virtual Hosts").
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class VirtualHostsModule(BaseModule):
    """List and manage virtual host (IP:port -> FQDN) configurations."""

    module_label = "virtual_hosts"

    def register_tools(self, server: FastMCP) -> None:
        self._add_tool(server, self.list_virtual_hosts, "list_virtual_hosts", tier="read")
        self._add_tool(server, self.manage_virtual_host, "manage_virtual_host", tier="write")
        self._add_tool(
            server, self.delete_virtual_host, "delete_virtual_host", tier="destructive"
        )

    def list_virtual_hosts(
        self,
        ip: str | None = None,
        port: int | None = None,
        echo_request: bool | None = None,
    ) -> dict[str, Any]:
        """List virtual hosts in the account.

        Args:
            ip: Restrict the list to virtual hosts with this IP address.
            port: Restrict the list to virtual hosts with this port.
            echo_request: Echo input parameters back in the output.

        Returns:
            Parsed VIRTUAL_HOST_LIST_OUTPUT (each entry has IP, PORT, FQDN).
        """
        params = {"action": "list", "ip": ip, "port": port, "echo_request": echo_request}
        return self._fo("/api/2.0/fo/asset/vhost/", method="GET", params=params)

    def manage_virtual_host(
        self,
        operation: str,
        ip: str,
        port: int,
        fqdn: str,
        network_id: str | None = None,
        echo_request: bool | None = None,
    ) -> dict[str, Any]:
        """Create, update, or add/remove FQDNs on a virtual host configuration.

        Args:
            operation: One of "create" (new virtual host), "update" (replace the
                FQDN list), "add_fqdn" (append FQDNs), or "delete_fqdn" (remove
                specific FQDNs). Use ``delete_virtual_host`` to remove the entire
                virtual host configuration.
            ip: The IP address for the virtual host configuration.
            port: The port number for the virtual host configuration.
            fqdn: One or more fully-qualified domain names, comma separated.
                Required for every operation supported by this method. Total
                bytes across all FQDNs (including commas) must stay under 4000.
            network_id: Network ID for the configuration (Network Support feature
                only; defaults to the Global Default Network).
            echo_request: Echo input parameters back in the output.

        Returns:
            SIMPLE_RETURN confirming the operation, or an error dict.
        """
        operation = operation.lower().strip()
        if operation not in ("create", "update", "add_fqdn", "delete_fqdn"):
            return {
                "error": "operation must be one of: create, update, add_fqdn, delete_fqdn"
            }
        data = {
            "action": operation,
            "ip": ip,
            "port": port,
            "fqdn": fqdn,
            "network_id": network_id,
            "echo_request": echo_request,
        }
        return self._fo("/api/2.0/fo/asset/vhost/", method="POST", data=data)

    def delete_virtual_host(
        self,
        ip: str,
        port: int,
        network_id: str | None = None,
        confirm: str | None = None,
    ) -> dict[str, Any]:
        """Permanently delete a virtual host configuration. IRREVERSIBLE.

        Args:
            ip: The IP address of the virtual host configuration to delete.
            port: The port number of the virtual host configuration to delete.
            network_id: Network ID for the configuration (Network Support feature
                only; defaults to the Global Default Network).
            confirm: Must equal ``"{ip}:{port}"`` to proceed.

        Returns:
            SIMPLE_RETURN confirming deletion, or a confirmation/error dict.
        """
        expected = f"{ip}:{port}"
        guard = self._confirm_or_error(confirm, expected=expected)
        if guard:
            return guard
        data = {
            "action": "delete",
            "ip": ip,
            "port": port,
            "network_id": network_id,
        }
        return self._fo("/api/2.0/fo/asset/vhost/", method="POST", data=data)
