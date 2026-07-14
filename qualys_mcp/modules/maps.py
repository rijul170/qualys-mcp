"""Discovery Scans (Maps) module (classic FO API).

Covers network discovery maps, scheduled scan/map tasks, and asset domains
(map targets):
* read  -> list_map_reports, list_running_maps, fetch_map_report,
           list_legacy_scheduled_tasks, list_domains
* write -> launch_map, cancel_map, create_legacy_scheduled_task, create_domain,
           update_domain
* destructive -> delete_map_report, delete_legacy_scheduled_task, delete_domain

Endpoints: ``/msp/map-2.php``, ``/msp/map_report_list.php``,
``/msp/scan_running_list.php``, ``/msp/scan_cancel.php``,
``/msp/map_report.php``, ``/msp/scan_report_delete.php``,
``/msp/scheduled_scans.php``, and the newer Domain V2 API
``/api/2.0/fo/asset/domain/`` (preferred over the legacy
``/msp/asset_domain.php`` add/edit-only endpoint since it supports list,
create, update, and delete).
Docs: Qualys VM/PC API User Guide — "Discovery Scans (maps)" / "Domain List" /
"Add/Edit Domain".
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class MapsModule(BaseModule):
    """Launch and manage discovery scans (maps), scheduled tasks, and domains."""

    module_label = "maps"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(server, self.list_map_reports, "list_map_reports", tier="read")
        self._add_tool(server, self.list_running_maps, "list_running_maps", tier="read")
        self._add_tool(server, self.fetch_map_report, "fetch_map_report", tier="read")
        self._add_tool(
            server, self.list_legacy_scheduled_tasks, "list_legacy_scheduled_tasks", tier="read"
        )
        self._add_tool(server, self.list_domains, "list_domains", tier="read")
        # Writes
        self._add_tool(server, self.launch_map, "launch_map", tier="write")
        self._add_tool(server, self.cancel_map, "cancel_map", tier="write")
        self._add_tool(
            server,
            self.create_legacy_scheduled_task,
            "create_legacy_scheduled_task",
            tier="write",
        )
        self._add_tool(server, self.create_domain, "create_domain", tier="write")
        self._add_tool(server, self.update_domain, "update_domain", tier="write")
        # Destructive (only registered if enable_destructive)
        self._add_tool(server, self.delete_map_report, "delete_map_report", tier="destructive")
        self._add_tool(
            server,
            self.delete_legacy_scheduled_task,
            "delete_legacy_scheduled_task",
            tier="destructive",
        )
        self._add_tool(server, self.delete_domain, "delete_domain", tier="destructive")

    # ------------------------------ reads ------------------------------ #
    def list_map_reports(
        self,
        domain: str | None = None,
        last: str | None = None,
    ) -> dict[str, Any]:
        """List saved network map reports in the user's account.

        Each entry identifies a saved map report for one target domain.

        Args:
            domain: Restrict to saved map reports for this target domain.
            last: Specify "yes" to retrieve only the last saved map report
                (per domain, if domain is also given); "no" (default) to
                retrieve all saved map reports.

        Returns:
            Parsed map report list output.
        """
        params = {"domain": domain, "last": last}
        return self._fo("/msp/map_report_list.php", method="GET", params=params)

    def list_running_maps(self) -> dict[str, Any]:
        """List maps and scans currently running in the user's account.

        For scans only (not maps), prefer the VM Scans module's list_scans
        tool.

        Returns:
            Parsed running scan/map list output.
        """
        return self._fo("/msp/scan_running_list.php", method="GET", params={})

    def fetch_map_report(self, ref: str) -> dict[str, Any]:
        """Download a saved map report (status must be "Finished").

        Args:
            ref: The map reference to download (e.g. "map/987659876.19876").

        Returns:
            Parsed map report output.
        """
        params = {"ref": ref}
        return self._fo("/msp/map_report.php", method="GET", params=params)

    def list_legacy_scheduled_tasks(self, task_type: str = "all") -> dict[str, Any]:
        """List scheduled scan and/or map tasks (legacy Scheduled Scans API).

        Args:
            task_type: "scan" for scheduled scans only, "map" for scheduled
                maps only, or "all" (default) for both.

        Returns:
            Parsed SCHEDULEDSCANS output listing matching tasks.
        """
        params = {"type": task_type}
        return self._fo("/msp/scheduled_scans.php", method="GET", params=params)

    def list_domains(self) -> dict[str, Any]:
        """List asset domains defined in the subscription (map targets).

        Uses the Domain V2 API. Managers see all domains; Unit Managers see
        domains in their business unit; Scanners/Readers see their own.

        Returns:
            Parsed DOMAIN_LIST (domain name, ID, network, and netblocks).
        """
        params = {"action": "list"}
        return self._fo("/api/2.0/fo/asset/domain/", method="GET", params=params)

    # ------------------------------ writes ----------------------------- #
    def launch_map(
        self,
        domain: str | None = None,
        asset_groups: str | None = None,
        map_title: str | None = None,
        iscanner_name: str | None = None,
        default_scanner: bool | None = None,
        option: str | None = None,
        network_id: int | None = None,
        save_report: str | None = None,
    ) -> dict[str, Any]:
        """Launch a network discovery map (asynchronous, one domain at a time).

        At least one of ``domain`` or ``asset_groups`` must be specified.

        Args:
            domain: Comma-separated domain name(s) for the map target. Do not
                prefix with "www.". A netblock may be appended per domain
                using a colon, e.g. "mycompany.com:192.168.0.1-192.168.0.254".
                Use "none:<netblock>" for a netblock with no domain.
            asset_groups: Comma-separated asset group titles for the map target.
            map_title: Title for the map, up to 2000 characters. Defaults to
                a standard descriptive title if unspecified.
            iscanner_name: Scanner appliance name, for private/internal IP
                targets. Mutually exclusive with default_scanner.
            default_scanner: Use the default scanner feature (only valid when
                the target is asset groups). Mutually exclusive with
                iscanner_name.
            option: Title of the option profile to apply. Defaults to the
                account's default option profile.
            network_id: Restrict to a custom network ID (requires Network
                Support feature). Defaults to "0" (Global Default Network).
            save_report: "yes" to save a map report per target domain on the
                Qualys server for later retrieval (recommended so the HTTP
                connection can close while the map runs); "no" (default) to
                not save.

        Returns:
            Parsed map report output (for save_report="no") or a confirmation
            that the map report was saved, per the map-2.dtd schema.
        """
        params = {
            "domain": domain,
            "asset_groups": asset_groups,
            "map_title": map_title,
            "iscanner_name": iscanner_name,
            "default_scanner": default_scanner,
            "option": option,
            "network_id": network_id,
            "save_report": save_report,
        }
        return self._fo("/msp/map-2.php", method="GET", params=params)

    def cancel_map(self, ref: str) -> dict[str, Any]:
        """Cancel a running map (or scan). Not possible while status is "Loading".

        Args:
            ref: The map reference to cancel (e.g. "map/987659876.19876"), or
                a scan reference for a running scan.

        Returns:
            Parsed generic_return confirming the cancellation, or an error.
        """
        params = {"ref": ref}
        return self._fo("/msp/scan_cancel.php", method="GET", params=params)

    def create_legacy_scheduled_task(
        self,
        scan_title: str,
        active: str,
        task_type: str = "scan",
        scan_target: str | None = None,
        asset_groups: str | None = None,
        exclude_ip_per_scan: str | None = None,
        iscanner_name: str | None = None,
        default_scanner: bool | None = None,
        scanners_in_ag: bool | None = None,
        option: str | None = None,
        occurrence: str | None = None,
        frequency_days: int | None = None,
        frequency_weeks: int | None = None,
        weekdays: str | None = None,
        frequency_months: int | None = None,
        day_of_month: int | None = None,
        day_of_week: int | None = None,
        week_of_month: str | None = None,
        time_zone_code: str | None = None,
        observe_dst: str | None = None,
        time_zone: int | None = None,
        start_date: str | None = None,
        start_hour: int = 0,
        start_minute: int = 0,
        end_after: int | None = None,
        recurrence: int | None = None,
    ) -> dict[str, Any]:
        """Add a scheduled scan or map task (legacy Scheduled Scans API).

        For a scheduled scan, target with scan_target (IPs/ranges) and/or
        asset_groups. For a scheduled map (task_type="map"), target with
        scan_target as one or more domain names and/or asset_groups.

        Args:
            scan_title: Title for the scheduled task (required).
            active: "yes" to make the task active, "no" to leave it inactive
                (required).
            task_type: "scan" (default) for a scheduled scan, or "map" for a
                scheduled map.
            scan_target: For a scan: IPs/ranges, comma separated. For a map:
                domain name(s), comma separated. One of scan_target/
                asset_groups is required.
            asset_groups: Comma-separated asset group titles for the task
                target. One of scan_target/asset_groups is required.
            exclude_ip_per_scan: IPs/ranges to exclude (scheduled scans only).
            iscanner_name: Scanner appliance name for private-IP targets.
                Mutually exclusive with default_scanner/scanners_in_ag.
            default_scanner: Use the default scanner feature (asset-group
                targets only). Mutually exclusive with iscanner_name/
                scanners_in_ag.
            scanners_in_ag: Use the scanners defined in each target asset
                group (scheduled scans only, not maps). Mutually exclusive
                with iscanner_name/default_scanner.
            option: Title of the option profile to apply, up to 64 characters.
                Defaults to the account's default option profile.
            occurrence: "daily", "weekly", or "monthly" (required to add a task).
            frequency_days: Run every N days, 1-365 (with occurrence="daily").
            frequency_weeks: Run every N weeks, 1-52 (with occurrence="weekly").
            weekdays: Comma-separated weekday names, e.g. "Sunday,Tuesday"
                (with occurrence="weekly").
            frequency_months: Run every N months, 1-12 (with occurrence="monthly").
            day_of_month: Day of month, 1-31, for a fixed-day monthly task.
            day_of_week: Day of week, 0 (Sunday) to 6 (Saturday), for an
                Nth-weekday monthly task (with week_of_month).
            week_of_month: "first", "second", "third", "fourth", or "last"
                (with day_of_week).
            time_zone_code: Time zone code, upper case (e.g. "US-CA"). One of
                time_zone_code/time_zone is required. See
                /msp/time_zone_code_list.php for valid codes.
            observe_dst: "yes" to observe Daylight Saving Time (only valid
                with a time_zone_code that supports DST).
            time_zone: GMT shift as an integer -12 to 12 (legacy alternative
                to time_zone_code; not valid for 30/45-minute-offset zones).
            start_date: Task start date, MM/DD/YYYY. Defaults to task
                creation date.
            start_hour: Hour the task starts, 0-23 (required). Default 0.
            start_minute: Minute the task starts, 0-59. Default 0.
            end_after: Deactivate the task if it hasn't completed after this
                many hours, 1-48. Default: never deactivate on duration.
            recurrence: Number of times to run before deactivating, 1-99.

        Returns:
            Parsed SCHEDULEDSCANS output for the newly added task (includes
            its assigned reference/task ID), or an error dict.
        """
        data = {
            "add_task": "yes",
            "scan_title": scan_title,
            "active": active,
            "type": task_type,
            "scan_target": scan_target,
            "asset_groups": asset_groups,
            "exclude_ip_per_scan": exclude_ip_per_scan,
            "iscanner_name": iscanner_name,
            "default_scanner": default_scanner,
            "scanners_in_ag": scanners_in_ag,
            "option": option,
            "occurrence": occurrence,
            "frequency_days": frequency_days,
            "frequency_weeks": frequency_weeks,
            "weekdays": weekdays,
            "frequency_months": frequency_months,
            "day_of_month": day_of_month,
            "day_of_week": day_of_week,
            "week_of_month": week_of_month,
            "time_zone_code": time_zone_code,
            "observe_dst": observe_dst,
            "time_zone": time_zone,
            "start_date": start_date,
            "start_hour": start_hour,
            "start_minute": start_minute,
            "end_after": end_after,
            "recurrence": recurrence,
        }
        return self._fo("/msp/scheduled_scans.php", method="POST", data=data)

    def create_domain(
        self, domain: str, netblock: str | None = None, network_id: int | None = None
    ) -> dict[str, Any]:
        """Add an asset domain (and optional netblocks) for use as a map target.

        Uses the Domain V2 API. Manager role required.

        Args:
            domain: The domain name to add (required).
            netblock: Comma-separated netblocks to associate with the domain.
            network_id: Custom network ID to add the domain to. Defaults to
                "0" (Global Default Network).

        Returns:
            SIMPLE_RETURN confirming the domain was created, or an error dict.
        """
        data = {"action": "create", "domain": domain, "netblock": netblock, "network_id": network_id}
        return self._fo("/api/2.0/fo/asset/domain/", method="POST", data=data)

    def update_domain(
        self,
        domain: str,
        netblock: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Update an existing asset domain's netblocks.

        Uses the Domain V2 API. Manager role required.

        Args:
            domain: The domain name (or ID) to update (required).
            netblock: Comma-separated netblocks to set on the domain. If
                omitted, Qualys clears the domain's associated netblocks.
            network_id: Custom network ID (requires Network Support feature).

        Returns:
            SIMPLE_RETURN confirming the domain was updated, or an error dict.
        """
        data = {"action": "update", "domain": domain, "netblock": netblock, "network_id": network_id}
        return self._fo("/api/2.0/fo/asset/domain/", method="POST", data=data)

    # --------------------------- destructive --------------------------- #
    def delete_map_report(self, ref: str, confirm: str | None = None) -> dict[str, Any]:
        """Permanently delete a saved network map report. IRREVERSIBLE.

        Gated: requires the console to be started with QUALYS_ENABLE_DESTRUCTIVE
        and the caller to pass confirm=<ref>.

        Args:
            ref: The map reference to delete (e.g. "map/999666888.12345").
            confirm: Must equal ``ref`` to proceed.

        Returns:
            Parsed generic_return confirming deletion, or a confirmation/error
            dict.
        """
        guard = self._confirm_or_error(confirm, expected=ref)
        if guard:
            return guard
        params = {"ref": ref}
        return self._fo("/msp/scan_report_delete.php", method="GET", params=params)

    def delete_legacy_scheduled_task(self, task_id: str, confirm: str | None = None) -> dict[str, Any]:
        """Permanently remove a scheduled scan or map task. IRREVERSIBLE.

        Saved reports produced by past runs of the task are not affected.

        Gated: requires the console to be started with QUALYS_ENABLE_DESTRUCTIVE
        and the caller to pass confirm=<task_id>.

        Args:
            task_id: The task ID to remove (assigned when the task was added).
            confirm: Must equal ``task_id`` to proceed.

        Returns:
            Parsed SCHEDULEDSCANS output confirming removal, or a
            confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=task_id)
        if guard:
            return guard
        data = {"drop_task": "yes", "task_id": task_id}
        return self._fo("/msp/scheduled_scans.php", method="POST", data=data)

    def delete_domain(self, ids: str, confirm: str | None = None) -> dict[str, Any]:
        """Permanently delete one or more asset domains. IRREVERSIBLE.

        Uses the Domain V2 API. Manager role required.

        Gated: requires the console to be started with QUALYS_ENABLE_DESTRUCTIVE
        and the caller to pass confirm=<ids>.

        Args:
            ids: Comma-separated domain ID(s) to delete (bulk delete supported).
            confirm: Must equal ``ids`` to proceed.

        Returns:
            SIMPLE_RETURN confirming deletion, or a confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=ids)
        if guard:
            return guard
        data = {"action": "delete", "ids": ids}
        return self._fo("/api/2.0/fo/asset/domain/", method="POST", data=data)
