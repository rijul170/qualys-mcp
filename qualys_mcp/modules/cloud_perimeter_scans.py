"""Cloud Perimeter Scans module (classic FO API).

Cloud perimeter scan jobs scan the public-facing (perimeter) footprint of a
cloud connector — e.g. public load balancers/EC2/App Gateways — for VM or PC.
Jobs are configured as create/update actions against a job resource; the same
job resource also appears in the VM Scan Schedule list filtered by
``scan_type=perimeter``.

* read  -> list_cloud_perimeter_scans
* write -> create_cloud_perimeter_scan, update_cloud_perimeter_scan,
           reset_cloud_perimeter_scan, launch_cloud_perimeter_scan

Endpoint: ``/api/4.0/fo/scan/cloud/perimeter/job/`` (latest active version;
v2.0/v3.0 are EOS). Schedule listing uses ``/api/2.0/fo/schedule/scan/``.
Docs: Qualys VM/PC API User Guide — "Cloud Perimeter Scans".
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class CloudPerimeterScansModule(BaseModule):
    """Create, update, and launch cloud perimeter scan jobs (VM/PC)."""

    module_label = "cloud_perimeter_scans"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(
            server, self.list_cloud_perimeter_scans, "list_cloud_perimeter_scans", tier="read"
        )
        # Writes
        self._add_tool(
            server, self.create_cloud_perimeter_scan, "create_cloud_perimeter_scan", tier="write"
        )
        self._add_tool(
            server, self.update_cloud_perimeter_scan, "update_cloud_perimeter_scan", tier="write"
        )
        self._add_tool(
            server, self.reset_cloud_perimeter_scan, "reset_cloud_perimeter_scan", tier="write"
        )
        self._add_tool(
            server, self.launch_cloud_perimeter_scan, "launch_cloud_perimeter_scan", tier="write"
        )

    # ------------------------------ reads ------------------------------ #
    def list_cloud_perimeter_scans(
        self,
        id: int | None = None,
        active: bool | None = None,
        show_notifications: bool | None = None,
        show_cloud_details: bool = True,
        client_id: int | None = None,
        client_name: str | None = None,
    ) -> dict[str, Any]:
        """List cloud perimeter scan jobs via the VM scan schedule list.

        Cloud perimeter jobs are schedule-backed; this filters the standard
        VM Scan Schedule list to perimeter jobs only (``scan_type=perimeter``).

        Args:
            id: Restrict to a single schedule/job ID.
            active: True for active schedules only, False for deactivated only.
            show_notifications: Include notification settings in the output.
            show_cloud_details: Include cloud details (Provider, Connector,
                Scan Type "Cloud Perimeter", Cloud Target). Default True.
            client_id: Consultant-type subscriptions only: client ID filter.
            client_name: Consultant-type subscriptions only: client name
                filter. Mutually exclusive with client_id.

        Returns:
            Parsed SCHEDULE_SCAN_LIST_OUTPUT filtered to perimeter jobs.
        """
        params = {
            "action": "list",
            "id": id,
            "active": active,
            "show_notifications": show_notifications,
            "scan_type": "perimeter",
            "show_cloud_details": show_cloud_details,
            "client_id": client_id,
            "client_name": client_name,
        }
        return self._fo("/api/2.0/fo/schedule/scan/", method="GET", params=params)

    # ------------------------------ writes ----------------------------- #
    def create_cloud_perimeter_scan(
        self,
        scan_title: str,
        module: str,
        cloud_provider: str,
        connector_name: str | None = None,
        connector_uuid: str | None = None,
        cloud_service: str | None = None,
        active: bool = True,
        option_id: int | None = None,
        option_title: str | None = None,
        priority: int | None = None,
        scanner_id: str | None = None,
        iscanner_name: str | None = None,
        platform_type: str | None = None,
        region_code: str | None = None,
        vpc_id: str | None = None,
        tag_set_by: str | None = None,
        tag_include_selector: str | None = None,
        tag_exclude_selector: str | None = None,
        tag_set_include: str | None = None,
        tag_set_exclude: str | None = None,
        elb_dns: str | None = None,
        schedule: str | None = None,
        occurrence: str | None = None,
        frequency_days: int | None = None,
        start_date: str | None = None,
        start_hour: int | None = None,
        start_minute: int | None = None,
        time_zone_code: str | None = None,
        include_lb_from_connector: bool | None = None,
        include_app_gateway_lb_from_connector: bool | None = None,
        configured_from_source: str | None = None,
        source_scan_type: str | None = None,
    ) -> dict[str, Any]:
        """Create a cloud perimeter scan job (VM or PC).

        The job is created even if no scan targets currently resolve; at scan
        time, an unresolved target logs an error instead of failing creation.

        Args:
            scan_title: Title for the scan job.
            module: "vm" or "pc" — which module runs the scan.
            cloud_provider: "aws", "azure", or "gcp".
            connector_name: Name of the cloud connector to use.
            connector_uuid: UUID of the cloud connector (alternative to
                connector_name).
            cloud_service: Cloud service type (e.g. "vm", "compute_engine").
            active: Whether the job is active. Default True.
            option_id: Option profile ID to use.
            option_title: Option profile title (alternative to option_id).
            priority: Scan processing priority 0-9 (0 = no priority).
            scanner_id: Scanner appliance ID.
            iscanner_name: Scanner appliance name.
            platform_type: e.g. "classic", "vpc_peered".
            region_code: Cloud region code (e.g. "us-east-1", "eastus").
            vpc_id: VPC ID to restrict scanning to (AWS).
            tag_set_by: "id" or "name" — how tag_set_include/exclude identify
                asset tags.
            tag_include_selector: "any" or "all" — included-tag match logic.
            tag_exclude_selector: "any" or "all" — excluded-tag match logic.
            tag_set_include: Comma-separated tag IDs/names to include.
            tag_set_exclude: Comma-separated tag IDs/names to exclude.
            elb_dns: Comma-separated ELB DNS names to include as targets.
            schedule: "now" for a one-time immediate job, or "recurring" for a
                repeating schedule (see occurrence/frequency_days/start_*).
            occurrence: "daily" (only daily is commonly used for perimeter
                jobs); required when schedule="recurring".
            frequency_days: Run every N days (1-365); required with
                occurrence="daily".
            start_date: Recurring schedule start date, MM/DD/YYYY.
            start_hour: Start hour, 0-23.
            start_minute: Start minute, 0-59.
            time_zone_code: Time zone code in upper case (e.g. "US-CA", "IN").
            include_lb_from_connector: Include public load balancers discovered
                by the connector as scan targets.
            include_app_gateway_lb_from_connector: Include public app gateway
                load balancers discovered by the connector as scan targets.
            configured_from_source: e.g. "connector_module" — origin of the
                job configuration.
            source_scan_type: e.g. "custom" — source scan type classification.

        Returns:
            SIMPLE_RETURN with the new job ID, or an error dict.
        """
        data = {
            "action": "create",
            "scan_title": scan_title,
            "module": module,
            "cloud_provider": cloud_provider,
            "connector_name": connector_name,
            "connector_uuid": connector_uuid,
            "cloud_service": cloud_service,
            "active": active,
            "option_id": option_id,
            "option_title": option_title,
            "priority": priority,
            "scanner_id": scanner_id,
            "iscanner_name": iscanner_name,
            "platform_type": platform_type,
            "region_code": region_code,
            "vpc_id": vpc_id,
            "tag_set_by": tag_set_by,
            "tag_include_selector": tag_include_selector,
            "tag_exclude_selector": tag_exclude_selector,
            "tag_set_include": tag_set_include,
            "tag_set_exclude": tag_set_exclude,
            "elb_dns": elb_dns,
            "schedule": schedule,
            "occurrence": occurrence,
            "frequency_days": frequency_days,
            "start_date": start_date,
            "start_hour": start_hour,
            "start_minute": start_minute,
            "time_zone_code": time_zone_code,
            "include_lb_from_connector": include_lb_from_connector,
            "include_app_gateway_lb_from_connector": include_app_gateway_lb_from_connector,
            "configured_from_source": configured_from_source,
            "source_scan_type": source_scan_type,
        }
        return self._fo("/api/4.0/fo/scan/cloud/perimeter/job/", method="POST", data=data)

    def update_cloud_perimeter_scan(
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
        scanner_id: str | None = None,
        iscanner_name: str | None = None,
        platform_type: str | None = None,
        region_code: str | None = None,
        vpc_id: str | None = None,
        tag_set_by: str | None = None,
        tag_include_selector: str | None = None,
        tag_exclude_selector: str | None = None,
        tag_set_include: str | None = None,
        tag_set_exclude: str | None = None,
        elb_dns: str | None = None,
        include_lb_from_connector: bool | None = None,
        include_app_gateway_lb_from_connector: bool | None = None,
    ) -> dict[str, Any]:
        """Update an existing cloud perimeter scan job.

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
            scanner_id: Scanner appliance ID.
            iscanner_name: Scanner appliance name.
            platform_type: e.g. "classic", "vpc_peered".
            region_code: Cloud region code.
            vpc_id: VPC ID to restrict scanning to (AWS).
            tag_set_by: "id" or "name".
            tag_include_selector: "any" or "all".
            tag_exclude_selector: "any" or "all".
            tag_set_include: Comma-separated tag IDs/names to include.
            tag_set_exclude: Comma-separated tag IDs/names to exclude.
            elb_dns: Comma-separated ELB DNS names to include as targets.
            include_lb_from_connector: Include public load balancers from the
                connector as scan targets.
            include_app_gateway_lb_from_connector: Include public app gateway
                load balancers from the connector as scan targets.

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
            "scanner_id": scanner_id,
            "iscanner_name": iscanner_name,
            "platform_type": platform_type,
            "region_code": region_code,
            "vpc_id": vpc_id,
            "tag_set_by": tag_set_by,
            "tag_include_selector": tag_include_selector,
            "tag_exclude_selector": tag_exclude_selector,
            "tag_set_include": tag_set_include,
            "tag_set_exclude": tag_set_exclude,
            "elb_dns": elb_dns,
            "include_lb_from_connector": include_lb_from_connector,
            "include_app_gateway_lb_from_connector": include_app_gateway_lb_from_connector,
        }
        return self._fo("/api/4.0/fo/scan/cloud/perimeter/job/", method="POST", data=data)

    def reset_cloud_perimeter_scan(
        self,
        id: int,
        remove_duration: bool = True,
        remove_recurrence: bool = True,
        active: bool | None = None,
    ) -> dict[str, Any]:
        """Reset a cloud perimeter scan job's pause/cancel duration and recurrence.

        Args:
            id: The job ID to reset.
            remove_duration: Clear the configured scan duration/pause-after
                setting. Default True.
            remove_recurrence: Clear the configured recurrence count. Default
                True.
            active: Optionally set the active flag while resetting.

        Returns:
            SIMPLE_RETURN confirming the update, or an error dict.
        """
        data = {
            "action": "update",
            "id": id,
            "remove_duration": remove_duration,
            "remove_recurrence": remove_recurrence,
            "active": active,
        }
        return self._fo("/api/4.0/fo/scan/cloud/perimeter/job/", method="POST", data=data)

    def launch_cloud_perimeter_scan(
        self,
        scan_title: str,
        module: str,
        cloud_provider: str,
        connector_name: str | None = None,
        connector_uuid: str | None = None,
        cloud_service: str | None = None,
        option_id: int | None = None,
        option_title: str | None = None,
        priority: int | None = None,
        scanner_id: str | None = None,
        iscanner_name: str | None = None,
        platform_type: str | None = None,
        region_code: str | None = None,
        vpc_id: str | None = None,
        tag_set_by: str | None = None,
        tag_include_selector: str | None = None,
        tag_exclude_selector: str | None = None,
        tag_set_include: str | None = None,
        tag_set_exclude: str | None = None,
        elb_dns: str | None = None,
        include_lb_from_connector: bool | None = None,
        include_app_gateway_lb_from_connector: bool | None = None,
        configured_from_source: str | None = None,
        source_scan_type: str | None = None,
    ) -> dict[str, Any]:
        """Launch a one-time (immediate) cloud perimeter scan job.

        Convenience wrapper around ``create_cloud_perimeter_scan`` that forces
        ``schedule="now"`` and ``active=1`` for an immediate, non-recurring run.

        Args:
            scan_title: Title for the scan job.
            module: "vm" or "pc" — which module runs the scan.
            cloud_provider: "aws", "azure", or "gcp".
            connector_name: Name of the cloud connector to use.
            connector_uuid: UUID of the cloud connector.
            cloud_service: Cloud service type (e.g. "vm", "compute_engine").
            option_id: Option profile ID to use.
            option_title: Option profile title (alternative to option_id).
            priority: Scan processing priority 0-9.
            scanner_id: Scanner appliance ID.
            iscanner_name: Scanner appliance name.
            platform_type: e.g. "classic", "vpc_peered".
            region_code: Cloud region code (e.g. "us-east-1").
            vpc_id: VPC ID to restrict scanning to (AWS).
            tag_set_by: "id" or "name".
            tag_include_selector: "any" or "all".
            tag_exclude_selector: "any" or "all".
            tag_set_include: Comma-separated tag IDs/names to include.
            tag_set_exclude: Comma-separated tag IDs/names to exclude.
            elb_dns: Comma-separated ELB DNS names to include as targets.
            include_lb_from_connector: Include public load balancers from the
                connector as scan targets.
            include_app_gateway_lb_from_connector: Include public app gateway
                load balancers from the connector as scan targets.
            configured_from_source: e.g. "connector_module".
            source_scan_type: e.g. "custom".

        Returns:
            SIMPLE_RETURN with the new job ID, or an error dict.
        """
        data = {
            "action": "create",
            "scan_title": scan_title,
            "module": module,
            "cloud_provider": cloud_provider,
            "connector_name": connector_name,
            "connector_uuid": connector_uuid,
            "cloud_service": cloud_service,
            "active": True,
            "schedule": "now",
            "option_id": option_id,
            "option_title": option_title,
            "priority": priority,
            "scanner_id": scanner_id,
            "iscanner_name": iscanner_name,
            "platform_type": platform_type,
            "region_code": region_code,
            "vpc_id": vpc_id,
            "tag_set_by": tag_set_by,
            "tag_include_selector": tag_include_selector,
            "tag_exclude_selector": tag_exclude_selector,
            "tag_set_include": tag_set_include,
            "tag_set_exclude": tag_set_exclude,
            "elb_dns": elb_dns,
            "include_lb_from_connector": include_lb_from_connector,
            "include_app_gateway_lb_from_connector": include_app_gateway_lb_from_connector,
            "configured_from_source": configured_from_source,
            "source_scan_type": source_scan_type,
        }
        return self._fo("/api/4.0/fo/scan/cloud/perimeter/job/", method="POST", data=data)
