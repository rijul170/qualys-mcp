"""Containerized Scanner Appliance module (classic FO API).

Covers create/list/update/delete for containerized scanner appliances
(QCSS). Mirrors the physical/virtual Scanner Appliance API but on its own
``/api/2.0/fo/appliance/qcss/`` endpoint.

Docs: Qualys VM/PC API User Guide — "Manage Containerized Scanner Appliance".
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule

_QCSS_PATH = "/api/2.0/fo/appliance/qcss/"


class ContainerizedScannerModule(BaseModule):
    """Create, list, update, and delete containerized scanner appliances."""

    module_label = "containerized_scanner"

    def register_tools(self, server: FastMCP) -> None:
        self._add_tool(
            server, self.list_containerized_scanners, "list_containerized_scanners", tier="read"
        )
        self._add_tool(
            server, self.create_containerized_scanner, "create_containerized_scanner", tier="write"
        )
        self._add_tool(
            server, self.update_containerized_scanner, "update_containerized_scanner", tier="write"
        )
        self._add_tool(
            server,
            self.delete_containerized_scanner,
            "delete_containerized_scanner",
            tier="destructive",
        )

    # ------------------------------------------------------------------ #
    # Reads
    # ------------------------------------------------------------------ #
    def list_containerized_scanners(
        self,
        output_mode: str = "brief",
        ids: str | None = None,
        name: str | None = None,
        busy: bool | None = None,
        scan_ref: str | None = None,
        appliance_type: str | None = None,
        platform_provider: str | None = None,
        scan_detail: bool | None = None,
        include_cloud_info: bool | None = None,
        include_license_info: bool | None = None,
        echo_request: bool | None = None,
    ) -> dict[str, Any]:
        """List containerized scanner appliances.

        Args:
            output_mode: "brief" (id, name, version, running scans, status)
                or "full" (all details, same as the Qualys UI).
            ids: Comma-separated appliance IDs to restrict output to.
            name: Substring match on appliance friendly name.
            busy: True to show only appliances currently running scans;
                False to show only idle appliances. Default (unset) shows
                all.
            scan_ref: Restrict to the appliance(s) running this scan
                reference (e.g. "scan/1234567890.12345").
            appliance_type: Filter by type: "physical", "containerized",
                "virtual", or "offline". Only applies when
                output_mode="full".
            platform_provider: Filter by cloud platform: "ec2", "ec2_compat",
                "gce", "azure", or "vCenter".
            scan_detail: Include scan ID/title/reference/type/date for scans
                currently running on each appliance.
            include_cloud_info: Include cloud platform details for
                cloud-deployed appliances (requires output_mode="full").
            include_license_info: Include license count info in the output.
            echo_request: Echo input parameters back in the XML output.

        Returns:
            Parsed APPLIANCE_LIST_OUTPUT.
        """
        data = {
            "action": "list",
            "output_mode": output_mode,
            "ids": ids,
            "name": name,
            "busy": busy,
            "scan_ref": scan_ref,
            "type": appliance_type,
            "platform_provider": platform_provider,
            "scan_detail": scan_detail,
            "include_cloud_info": include_cloud_info,
            "include_license_info": include_license_info,
            "echo_request": echo_request,
        }
        # Qualys documents this action as POST-only (unlike the physical/
        # virtual appliance list, which also accepts GET).
        return self._fo(_QCSS_PATH, method="POST", data=data)

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #
    def create_containerized_scanner(
        self,
        name: str,
        polling_interval: int | None = None,
        asset_group_id: int | None = None,
        echo_request: bool | None = None,
    ) -> dict[str, Any]:
        """Create a new containerized scanner appliance.

        Args:
            name: Friendly name for the appliance. Must be unique in the
                account, max 32 characters, no spaces.
            polling_interval: Seconds between platform check-ins, 60-3600
                (default/recommended 180).
            asset_group_id: Asset group ID to assign the scanner to
                (required for Unit Manager / Scanner callers).
            echo_request: Echo input parameters back in the XML output.

        Returns:
            APPLIANCE_CREATE_OUTPUT with the new appliance ID and activation
            code, or an error dict.
        """
        data = {
            "action": "create",
            "name": name,
            "polling_interval": polling_interval,
            "asset_group_id": asset_group_id,
            "echo_request": echo_request,
        }
        return self._fo(_QCSS_PATH, method="POST", data=data)

    def update_containerized_scanner(
        self,
        appliance_id: int,
        name: str | None = None,
        polling_interval: int | None = None,
        comment: str | None = None,
        set_tags: str | None = None,
        add_tags: str | None = None,
        remove_tags: str | None = None,
        tag_set_by: str | None = None,
        enable_ipv6: bool | None = None,
        echo_request: bool | None = None,
    ) -> dict[str, Any]:
        """Update a containerized scanner appliance's settings and/or tags.

        Args:
            appliance_id: ID of the containerized scanner to update.
            name: New friendly name (must be unique, max 32 chars, no
                spaces).
            polling_interval: Seconds between platform check-ins, 60-3600.
            comment: User-defined comment.
            set_tags: Replace all tags with this comma-separated set.
                Mutually exclusive with add_tags/remove_tags.
            add_tags: Comma-separated tags to add to the existing tag set.
                Mutually exclusive with set_tags.
            remove_tags: Comma-separated tags to remove from the existing tag
                set. Mutually exclusive with set_tags.
            tag_set_by: "id" (default) or "name".
            enable_ipv6: Enable (True) or disable (False) IPv6 on LAN.
            echo_request: Echo input parameters back in the XML output.

        Returns:
            SIMPLE_RETURN status ("Containerized scanner updated
            successfully"), or an error dict.
        """
        data = {
            "action": "update",
            "id": appliance_id,
            "name": name,
            "polling_interval": polling_interval,
            "comment": comment,
            "set_tags": set_tags,
            "add_tags": add_tags,
            "remove_tags": remove_tags,
            "tag_set_by": tag_set_by,
            "enable_ipv6": enable_ipv6,
            "echo_request": echo_request,
        }
        return self._fo(_QCSS_PATH, method="POST", data=data)

    # ------------------------------------------------------------------ #
    # Destructive
    # ------------------------------------------------------------------ #
    def delete_containerized_scanner(
        self, appliance_id: int, confirm: str | None = None
    ) -> dict[str, Any]:
        """Permanently delete a containerized scanner appliance. IRREVERSIBLE.

        Deleting removes the scanner from associated asset groups and
        deactivates scheduled scans that use it.

        Args:
            appliance_id: ID of the containerized scanner to delete.
            confirm: Must equal ``str(appliance_id)`` to proceed.

        Returns:
            SIMPLE_RETURN status (deactivated scans / affected asset groups),
            or a confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=str(appliance_id))
        if guard:
            return guard
        data = {"action": "delete", "id": appliance_id}
        return self._fo(_QCSS_PATH, method="POST", data=data)
