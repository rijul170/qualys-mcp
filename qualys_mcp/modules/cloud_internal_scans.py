"""Cloud Internal Scans module (classic FO API).

Cloud internal scan jobs scan assets inside a cloud virtual network (Azure
VMs, GCP Compute Engine instances) reachable via an internal scanner. Jobs are
configured as create/update actions against a job resource; the same job
resource also appears in the VM Scan Schedule list filtered by
``scan_type=internal``.

* read  -> list_cloud_internal_scans
* write -> create_cloud_internal_scan, update_cloud_internal_scan

Endpoint: ``/api/3.0/fo/scan/cloud/internal/job/`` (v3.0 is the current,
unrestricted version; v2.0 is EOS November 2026 / EOL May 2027).
Docs: Qualys VM/PC API User Guide — "Cloud Internal Scans".
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class CloudInternalScansModule(BaseModule):
    """Create, update, and list Azure/GCP cloud internal scan jobs (VM only)."""

    module_label = "cloud_internal_scans"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(
            server, self.list_cloud_internal_scans, "list_cloud_internal_scans", tier="read"
        )
        # Writes
        self._add_tool(
            server, self.create_cloud_internal_scan, "create_cloud_internal_scan", tier="write"
        )
        self._add_tool(
            server, self.update_cloud_internal_scan, "update_cloud_internal_scan", tier="write"
        )

    # ------------------------------ reads ------------------------------ #
    def list_cloud_internal_scans(
        self,
        id: int | None = None,
        active: bool | None = None,
        show_notifications: bool | None = None,
        show_cloud_details: bool = True,
    ) -> dict[str, Any]:
        """List cloud internal scan jobs (Azure/GCP) via the VM scan schedule list.

        Cloud internal jobs are schedule-backed; this filters the standard VM
        Scan Schedule list to internal jobs only (``scan_type=internal``).

        Args:
            id: Restrict to a single schedule/job ID.
            active: True for active schedules only, False for deactivated only.
            show_notifications: Include notification settings in the output.
            show_cloud_details: Include cloud details (Provider, Connector,
                Scan Type "Cloud Internal", Cloud Target). Default True.

        Returns:
            Parsed SCHEDULE_SCAN_LIST_OUTPUT filtered to internal jobs.
        """
        params = {
            "action": "list",
            "id": id,
            "active": active,
            "show_notifications": show_notifications,
            "scan_type": "internal",
            "show_cloud_details": show_cloud_details,
        }
        return self._fo("/api/3.0/fo/schedule/scan/", method="GET", params=params)

    # ------------------------------ writes ----------------------------- #
    def create_cloud_internal_scan(
        self,
        scan_title: str,
        cloud_provider: str,
        module: str = "vm",
        connector_name: str | None = None,
        connector_uuid: str | None = None,
        cloud_service: str | None = None,
        active: bool = True,
        option_id: int | None = None,
        option_title: str | None = None,
        priority: int | None = None,
        iscanner_id: str | None = None,
        iscanner_name: str | None = None,
        platform_type: str | None = None,
        region_code: str | None = None,
        virtual_network_id: str | None = None,
        cloud_resource_ids: str | None = None,
        tag_set_by: str | None = None,
        tag_include_selector: str | None = None,
        tag_exclude_selector: str | None = None,
        tag_set_include: str | None = None,
        tag_set_exclude: str | None = None,
        schedule: str | None = None,
    ) -> dict[str, Any]:
        """Create an Azure or GCP cloud internal scan job.

        The job is created even if no scan targets currently resolve; at scan
        time, an unresolved target logs an error instead of failing creation.

        Args:
            scan_title: Title for the scan job.
            cloud_provider: "azure" or "gcp".
            module: Module to run the scan in. Only "vm" is supported for
                cloud internal scans.
            connector_name: Name of the cloud connector to use.
            connector_uuid: UUID of the cloud connector (alternative to
                connector_name).
            cloud_service: Cloud service type (e.g. "vm" for Azure,
                "compute_engine" for GCP).
            active: Whether the job is active. Default True.
            option_id: Option profile ID to use.
            option_title: Option profile title (alternative to option_id).
            priority: Scan processing priority 0-9 (0 = no priority).
            iscanner_id: Internal scanner appliance ID.
            iscanner_name: Internal scanner appliance name (an internal Azure/
                GCP scanner must be reachable from the target network).
            platform_type: e.g. "location" (Azure region-based placement).
            region_code: Cloud region code (e.g. "eastus", "us-central1").
            virtual_network_id: Cloud virtual network identifier — Azure VNet
                ID or GCP fully-qualified network path (e.g.
                "projects/<proj>/virtualNetworks/<vpc>").
            cloud_resource_ids: Comma-separated cloud resource IDs to restrict
                the job to (e.g. specific regions for GCP updates).
            tag_set_by: "id" or "name" — how tag_set_include/exclude identify
                asset tags.
            tag_include_selector: "any" or "all" — included-tag match logic.
            tag_exclude_selector: "any" or "all" — excluded-tag match logic.
            tag_set_include: Comma-separated tag IDs/names to include.
            tag_set_exclude: Comma-separated tag IDs/names to exclude.
            schedule: "now" for a one-time immediate job, or "recurring" for a
                repeating schedule.

        Returns:
            SIMPLE_RETURN with the new job ID, or an error dict.
        """
        data = {
            "action": "create",
            "scan_title": scan_title,
            "cloud_provider": cloud_provider,
            "module": module,
            "connector_name": connector_name,
            "connector_uuid": connector_uuid,
            "cloud_service": cloud_service,
            "active": active,
            "option_id": option_id,
            "option_title": option_title,
            "priority": priority,
            "iscanner_id": iscanner_id,
            "iscanner_name": iscanner_name,
            "platform_type": platform_type,
            "region_code": region_code,
            "virtual_network_id": virtual_network_id,
            "cloud_resource_ids": cloud_resource_ids,
            "tag_set_by": tag_set_by,
            "tag_include_selector": tag_include_selector,
            "tag_exclude_selector": tag_exclude_selector,
            "tag_set_include": tag_set_include,
            "tag_set_exclude": tag_set_exclude,
            "schedule": schedule,
        }
        return self._fo("/api/3.0/fo/scan/cloud/internal/job/", method="POST", data=data)

    def update_cloud_internal_scan(
        self,
        id: int,
        scan_title: str | None = None,
        connector_name: str | None = None,
        connector_uuid: str | None = None,
        cloud_service: str | None = None,
        active: bool | None = None,
        option_id: int | None = None,
        option_title: str | None = None,
        priority: int | None = None,
        iscanner_id: str | None = None,
        iscanner_name: str | None = None,
        platform_type: str | None = None,
        region_code: str | None = None,
        virtual_network_id: str | None = None,
        cloud_resource_ids: str | None = None,
        tag_set_by: str | None = None,
        tag_include_selector: str | None = None,
        tag_exclude_selector: str | None = None,
        tag_set_include: str | None = None,
        tag_set_exclude: str | None = None,
        schedule: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing Azure or GCP cloud internal scan job.

        Args:
            id: The job ID to update (as returned by create).
            scan_title: New title for the scan job.
            connector_name: Name of the cloud connector to use.
            connector_uuid: UUID of the cloud connector.
            cloud_service: Cloud service type.
            active: Whether the job is active.
            option_id: Option profile ID to use.
            option_title: Option profile title.
            priority: Scan processing priority 0-9.
            iscanner_id: Internal scanner appliance ID.
            iscanner_name: Internal scanner appliance name.
            platform_type: e.g. "location".
            region_code: Cloud region code.
            virtual_network_id: Cloud virtual network identifier.
            cloud_resource_ids: Comma-separated cloud resource IDs to restrict
                the job to.
            tag_set_by: "id" or "name".
            tag_include_selector: "any" or "all".
            tag_exclude_selector: "any" or "all".
            tag_set_include: Comma-separated tag IDs/names to include.
            tag_set_exclude: Comma-separated tag IDs/names to exclude.
            schedule: "now" or "recurring".

        Returns:
            SIMPLE_RETURN confirming the update, or an error dict.
        """
        data = {
            "action": "update",
            "id": id,
            "scan_title": scan_title,
            "connector_name": connector_name,
            "connector_uuid": connector_uuid,
            "cloud_service": cloud_service,
            "active": active,
            "option_id": option_id,
            "option_title": option_title,
            "priority": priority,
            "iscanner_id": iscanner_id,
            "iscanner_name": iscanner_name,
            "platform_type": platform_type,
            "region_code": region_code,
            "virtual_network_id": virtual_network_id,
            "cloud_resource_ids": cloud_resource_ids,
            "tag_set_by": tag_set_by,
            "tag_include_selector": tag_include_selector,
            "tag_exclude_selector": tag_exclude_selector,
            "tag_set_include": tag_set_include,
            "tag_set_exclude": tag_set_exclude,
            "schedule": schedule,
        }
        return self._fo("/api/3.0/fo/scan/cloud/internal/job/", method="POST", data=data)
