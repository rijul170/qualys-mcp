"""Scanner Appliances module (classic FO API).

Covers listing, creating/updating/deleting virtual scanner appliances,
updating physical scanner appliances, replacing a scanner appliance, and
managing VLANs/static routes on a scanner appliance.

Endpoints:
* ``/api/2.0/fo/appliance/`` (list, virtual create/update/delete, VLANs/routes)
* ``/api/2.0/fo/appliance/physical/`` (physical update, VLANs/routes)
* ``/api/2.0/fo/appliance/replace_iscanner/`` (replace)

Docs: Qualys VM/PC API User Guide — "Scanner Appliance List", "Manage Virtual
Scanner Appliances", "Update Physical Scanner Appliance", "Replace Scanner
Appliance", "Scanner Appliance VLANs and Static Routes".
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class ScannerAppliancesModule(BaseModule):
    """List and manage Qualys scanner appliances (virtual and physical)."""

    module_label = "scanner_appliances"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(server, self.list_scanner_appliances, "list_scanner_appliances", tier="read")
        self._add_tool(
            server, self.get_scanner_vlans_routes, "get_scanner_vlans_routes", tier="read"
        )
        # Writes
        self._add_tool(server, self.create_virtual_scanner, "create_virtual_scanner", tier="write")
        self._add_tool(server, self.update_virtual_scanner, "update_virtual_scanner", tier="write")
        self._add_tool(server, self.update_physical_scanner, "update_physical_scanner", tier="write")
        self._add_tool(server, self.replace_scanner_appliance, "replace_scanner_appliance", tier="write")
        self._add_tool(server, self.set_scanner_vlans, "set_scanner_vlans", tier="write")
        self._add_tool(server, self.set_scanner_routes, "set_scanner_routes", tier="write")
        # Destructive
        self._add_tool(server, self.delete_virtual_scanner, "delete_virtual_scanner", tier="destructive")

    # ------------------------------------------------------------------ #
    # Reads
    # ------------------------------------------------------------------ #
    def list_scanner_appliances(
        self,
        output_mode: str = "brief",
        ids: str | None = None,
        name: str | None = None,
        busy: bool | None = None,
        scan_ref: str | None = None,
        scanner_type: str | None = None,
        platform_provider: str | None = None,
        scan_detail: bool | None = None,
        show_tags: bool | None = None,
        include_cloud_info: bool | None = None,
        include_license_info: bool | None = None,
    ) -> dict[str, Any]:
        """List scanner appliances (physical, virtual, containerized, offline).

        Args:
            output_mode: "brief" (id, name, version, running scans, status) or
                "full" (all details, same as the Qualys UI).
            ids: Comma-separated appliance IDs to restrict output to.
            name: Substring match on appliance friendly name.
            busy: True to show only appliances currently running scans; False
                to show only idle appliances. Default (None/unset) shows all.
            scan_ref: Restrict to the appliance(s) running this scan
                reference (e.g. "scan/1234567890.12345", "compliance/...",
                "was/...", "qscap/...", "map/...").
            scanner_type: Filter by type: "physical", "virtual",
                "containerized", or "offline". Only applies when
                output_mode="full".
            platform_provider: Filter by cloud platform: "ec2" (Amazon EC2),
                "ec2_compat" (OpenStack), "gce" (Google Cloud), "azure"
                (Microsoft Azure), or "vCenter" (VMware vCenter).
            scan_detail: Include scan ID/title/reference/type/date for scans
                currently running on each appliance.
            show_tags: Include asset tag info per appliance (requires
                output_mode="full"). Default True per the API.
            include_cloud_info: Include cloud platform details (instance ID,
                region, etc) for cloud-deployed virtual appliances (requires
                output_mode="full").
            include_license_info: Include virtual scanner license counts
                (QVSA_LICENSES_COUNT / QVSA_LICENSES_USED) in the output.

        Returns:
            Parsed APPLIANCE_LIST_OUTPUT.
        """
        params = {
            "action": "list",
            "output_mode": output_mode,
            "ids": ids,
            "name": name,
            "busy": busy,
            "scan_ref": scan_ref,
            "type": scanner_type,
            "platform_provider": platform_provider,
            "scan_detail": scan_detail,
            "show_tags": show_tags,
            "include_cloud_info": include_cloud_info,
            "include_license_info": include_license_info,
        }
        return self._fo("/api/2.0/fo/appliance/", method="GET", params=params)

    def get_scanner_vlans_routes(self, ids: str | None = None) -> dict[str, Any]:
        """View VLANs and static routes configured on scanner appliance(s).

        Convenience wrapper around ``list_scanner_appliances`` with
        ``output_mode="full"``, since VLAN/static-route settings only appear
        in full-detail output (``VLANS`` / ``STATIC_ROUTES`` elements).

        Args:
            ids: Comma-separated appliance IDs to restrict output to. When
                omitted, all appliances are returned (may be large).

        Returns:
            Parsed APPLIANCE_LIST_OUTPUT including VLANS and STATIC_ROUTES.
        """
        params = {"action": "list", "output_mode": "full", "ids": ids}
        return self._fo("/api/2.0/fo/appliance/", method="GET", params=params)

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #
    def create_virtual_scanner(
        self,
        name: str,
        polling_interval: int | None = None,
        asset_group_id: int | None = None,
        echo_request: bool | None = None,
    ) -> dict[str, Any]:
        """Create a new virtual scanner appliance.

        Args:
            name: Friendly name for the appliance. Must be unique in the
                account, max 15 characters, no spaces.
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
        return self._fo("/api/2.0/fo/appliance/", method="POST", data=data)

    def update_virtual_scanner(
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
        """Update a virtual scanner appliance's settings and/or tags.

        Args:
            appliance_id: ID of the virtual scanner to update.
            name: New friendly name (must be unique, max 15 chars, no spaces).
            polling_interval: Seconds between platform check-ins, 60-3600.
            comment: User-defined comment.
            set_tags: Replace all tags on the appliance with this
                comma-separated set. Mutually exclusive with add_tags/remove_tags.
            add_tags: Comma-separated tags to add to the existing tag set.
                Mutually exclusive with set_tags.
            remove_tags: Comma-separated tags to remove from the existing tag
                set. Mutually exclusive with set_tags.
            tag_set_by: "id" (default) or "name" — whether set_tags/add_tags/
                remove_tags identify tags by ID or by name.
            enable_ipv6: Enable (True) or disable (False) IPv6 on LAN.
            echo_request: Echo input parameters back in the XML output.

        Returns:
            SIMPLE_RETURN status ("Virtual scanner updated successfully"), or
            an error dict.
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
        return self._fo("/api/2.0/fo/appliance/", method="POST", data=data)

    def update_physical_scanner(
        self,
        appliance_id: int,
        name: str | None = None,
        polling_interval: int | None = None,
        comment: str | None = None,
        set_tags: str | None = None,
        add_tags: str | None = None,
        remove_tags: str | None = None,
        tag_set_by: str | None = None,
        set_vlans: str | None = None,
        set_routes: str | None = None,
        echo_request: bool | None = None,
    ) -> dict[str, Any]:
        """Update a physical scanner appliance's settings, tags, VLANs, or routes.

        Args:
            appliance_id: ID of the physical scanner to update.
            name: New friendly name (must be unique, max 15 chars, no spaces).
            polling_interval: Seconds between platform check-ins, 60-3600.
            comment: User-defined comment.
            set_tags: Replace all tags with this comma-separated set.
                Mutually exclusive with add_tags/remove_tags.
            add_tags: Comma-separated tags to add. Mutually exclusive with
                set_tags.
            remove_tags: Comma-separated tags to remove. Mutually exclusive
                with set_tags.
            tag_set_by: "id" (default) or "name".
            set_vlans: VLAN spec(s); see ``set_scanner_vlans`` for format.
                Pass "" (empty string) to remove all VLANs.
            set_routes: Static route spec(s); see ``set_scanner_routes`` for
                format. Pass "" (empty string) to remove all routes.
            echo_request: Echo input parameters back in the XML output.

        Returns:
            SIMPLE_RETURN status ("Physical scanner updated successfully"),
            or an error dict.
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
            "set_vlans": set_vlans,
            "set_routes": set_routes,
            "echo_request": echo_request,
        }
        return self._fo("/api/2.0/fo/appliance/physical/", method="POST", data=data)

    def replace_scanner_appliance(
        self,
        old_scanner_name: str,
        new_scanner_name: str,
        do_not_copy_settings: bool | None = None,
        do_not_remove_new_scanner_from_objects: bool | None = None,
        echo_request: bool | None = None,
    ) -> dict[str, Any]:
        """Replace one scanner appliance with another.

        Good to know: only one replacement at a time; do not replace while
        scans using the appliance are in progress; old and new scanners must
        be on the same network (if applicable); EC2 scanners can only be
        replaced by other EC2 scanners.

        Args:
            old_scanner_name: Name of the scanner appliance to replace.
            new_scanner_name: Name of the scanner appliance to use instead.
            do_not_copy_settings: By default, settings (polling interval,
                heartbeat, scan options, VLANs/routes, asset groups,
                schedules, network) are copied from old to new. Set True to
                skip copying settings.
            do_not_remove_new_scanner_from_objects: By default, the new
                appliance is removed from asset groups/schedules it was
                already associated with. Set True to skip this removal.
                Cannot be set for EC2 scanners.
            echo_request: Echo input parameters back in the XML output.

        Returns:
            SCANNER_REPLACE_OUTPUT with new settings/scheduled scans/asset
            groups affected, or an error dict.
        """
        params = {
            "action": "replace",
            "old_scanner_name": old_scanner_name,
            "new_scanner_name": new_scanner_name,
            "do_not_copy_settings": do_not_copy_settings,
            "do_not_remove_new_scanner_from_objects": do_not_remove_new_scanner_from_objects,
            "echo_request": echo_request,
        }
        return self._fo("/api/2.0/fo/appliance/replace_iscanner/", method="GET", params=params)

    def set_scanner_vlans(
        self,
        appliance_id: int,
        set_vlans: str,
        physical: bool = False,
    ) -> dict[str, Any]:
        """Set (add/update/remove) VLANs on a scanner appliance.

        Requires the VLANs and Static Routes feature to be enabled on the
        subscription.

        Args:
            appliance_id: ID of the scanner appliance (virtual or physical).
            set_vlans: Comma-separated VLAN specs. Each VLAN is
                ``ID|IPv4_ADDRESS|NETMASK|NAME|ipv6_static_or_ipv6_auto|IPv6_ADDRESS``
                (pipe-delimited; all fields required, may be empty strings
                where not applicable). ID is a customer-defined value 0-4096.
                Pass "" (empty string) to remove *all* VLANs on the appliance.
            physical: False (default) to target a virtual scanner appliance
                (``/api/2.0/fo/appliance/``); True to target a physical
                scanner appliance (``/api/2.0/fo/appliance/physical/``).

        Returns:
            SIMPLE_RETURN status, or an error dict.
        """
        path = "/api/2.0/fo/appliance/physical/" if physical else "/api/2.0/fo/appliance/"
        data = {"action": "update", "id": appliance_id, "set_vlans": set_vlans}
        return self._fo(path, method="POST", data=data)

    def set_scanner_routes(
        self,
        appliance_id: int,
        set_routes: str,
        physical: bool = False,
    ) -> dict[str, Any]:
        """Set (add/update/remove) static routes on a scanner appliance.

        Requires the VLANs and Static Routes feature to be enabled on the
        subscription.

        Args:
            appliance_id: ID of the scanner appliance (virtual or physical).
            set_routes: Comma-separated static route specs. Each route is
                ``IPv4_ADDRESS|NETMASK|IPv4_GATEWAY|NAME|IPv6_ADDRESS|IPv6_GATEWAY``
                (pipe-delimited; all fields required, may be empty strings
                where not applicable). Pass "" (empty string) to remove *all*
                static routes on the appliance.
            physical: False (default) to target a virtual scanner appliance
                (``/api/2.0/fo/appliance/``); True to target a physical
                scanner appliance (``/api/2.0/fo/appliance/physical/``).

        Returns:
            SIMPLE_RETURN status, or an error dict.
        """
        path = "/api/2.0/fo/appliance/physical/" if physical else "/api/2.0/fo/appliance/"
        data = {"action": "update", "id": appliance_id, "set_routes": set_routes}
        return self._fo(path, method="POST", data=data)

    # ------------------------------------------------------------------ #
    # Destructive
    # ------------------------------------------------------------------ #
    def delete_virtual_scanner(
        self, appliance_id: int, confirm: str | None = None
    ) -> dict[str, Any]:
        """Permanently delete a virtual scanner appliance. IRREVERSIBLE.

        Deleting removes the scanner from associated asset groups and
        deactivates scheduled scans that use it. Fails if the scanner is
        currently running scans.

        Args:
            appliance_id: ID of the virtual scanner to delete.
            confirm: Must equal ``str(appliance_id)`` to proceed.

        Returns:
            SIMPLE_RETURN status (deactivated scans / affected asset groups),
            or a confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=str(appliance_id))
        if guard:
            return guard
        data = {"action": "delete", "id": appliance_id}
        return self._fo("/api/2.0/fo/appliance/", method="POST", data=data)
