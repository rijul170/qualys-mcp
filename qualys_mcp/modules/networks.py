"""Networks module (classic FO API) — custom network management.

Covers:
* Network List (``/api/2.0/fo/network/`` action=list).
* Create Network (``/api/2.0/fo/network/`` action=create).
* Update Network (``/api/2.0/fo/network/`` action=update).
* Assign Scanner Appliance to Network (``/api/2.0/fo/appliance/`` action=assign_network_id).

Requires the Network Support feature to be enabled for the subscription.

Docs: Qualys VM/PC API User Guide — "Networks" chapter.
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class NetworksModule(BaseModule):
    """List, create, and update custom networks; assign scanner appliances to them."""

    module_label = "networks"

    def register_tools(self, server: FastMCP) -> None:
        self._add_tool(server, self.list_networks, "list_networks", tier="read")
        self._add_tool(server, self.create_network, "create_network", tier="write")
        self._add_tool(server, self.update_network, "update_network", tier="write")
        self._add_tool(
            server,
            self.assign_scanner_appliance_to_network,
            "assign_scanner_appliance_to_network",
            tier="write",
        )

    def list_networks(
        self, ids: str | None = None, echo_request: bool | None = None
    ) -> dict[str, Any]:
        """List custom networks in the subscription.

        Args:
            ids: Comma-separated network IDs to restrict the list to.
            echo_request: Echo input parameters back in the output.

        Returns:
            Parsed NETWORK_LIST output (each entry includes its scanner
            appliance assignments).
        """
        params = {"action": "list", "ids": ids, "echo_request": echo_request}
        return self._fo("/api/2.0/fo/network/", method="GET", params=params)

    def create_network(
        self, name: str, echo_request: bool | None = None
    ) -> dict[str, Any]:
        """Create a new custom network.

        After creating a network you'll need to 1) assign scanner appliance(s)
        to it (see ``assign_scanner_appliance_to_network``), and 2) add host
        assets to it by assigning asset groups.

        Args:
            name: A user-defined friendly name for the network.
            echo_request: Echo input parameters back in the output.

        Returns:
            SIMPLE_RETURN with the new network ID (``ITEM_LIST`` key "id"), or
            an error dict.
        """
        data = {"action": "create", "name": name, "echo_request": echo_request}
        return self._fo("/api/2.0/fo/network/", method="POST", data=data)

    def update_network(
        self, id: str, name: str, echo_request: bool | None = None
    ) -> dict[str, Any]:
        """Rename an existing custom network. The network ID itself cannot change.

        Args:
            id: The ID of the network to update.
            name: The new network name.
            echo_request: Echo input parameters back in the output.

        Returns:
            SIMPLE_RETURN confirming the update (``ITEM_LIST`` keys "id", "name"),
            or an error dict.
        """
        data = {"id": id, "action": "update", "name": name, "echo_request": echo_request}
        return self._fo("/api/2.0/fo/network/", method="POST", data=data)

    def assign_scanner_appliance_to_network(
        self, appliance_id: str, network_id: str, echo_request: bool | None = None
    ) -> dict[str, Any]:
        """Assign a scanner appliance to a custom network.

        Each scanner appliance can be assigned to exactly one network.

        Args:
            appliance_id: The ID of the scanner appliance to assign.
            network_id: The ID of the network to assign the appliance to.
            echo_request: Echo input parameters back in the output.

        Returns:
            SIMPLE_RETURN confirming the assignment, or an error dict.
        """
        data = {
            "action": "assign_network_id",
            "appliance_id": appliance_id,
            "network_id": network_id,
            "echo_request": echo_request,
        }
        return self._fo("/api/2.0/fo/appliance/", method="POST", data=data)
