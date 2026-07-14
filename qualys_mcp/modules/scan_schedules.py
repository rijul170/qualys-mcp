"""Scan Schedules module (classic FO API).

Covers recurring VM scan schedules and Policy Compliance (PC) scan schedules:
* read  -> list_vm_scan_schedules, list_compliance_scan_schedules
* write -> create_vm_scan_schedule, update_vm_scan_schedule,
           create_compliance_scan_schedule, update_compliance_scan_schedule
* destructive -> delete_vm_scan_schedule, delete_compliance_scan_schedule

Endpoints: ``/api/5.0/fo/schedule/scan/`` for listing (latest active version;
v2.0-v4.0 are EOS), ``/api/2.0/fo/schedule/scan/`` for create/update/delete
(no newer version documented for these actions), and
``/api/2.0/fo/schedule/scan/compliance/`` for PC schedules (single version).
Docs: Qualys VM/PC API User Guide — "VM Scan Schedules" / "PC Scan Schedules".
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class ScanSchedulesModule(BaseModule):
    """Create, update, list, and delete VM and PC recurring scan schedules."""

    module_label = "scan_schedules"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(server, self.list_vm_scan_schedules, "list_vm_scan_schedules", tier="read")
        self._add_tool(
            server,
            self.list_compliance_scan_schedules,
            "list_compliance_scan_schedules",
            tier="read",
        )
        self._add_tool(
            server,
            self.list_vm_schedule_run_history,
            "list_vm_schedule_run_history",
            tier="read",
        )
        self._add_tool(
            server,
            self.list_compliance_schedule_run_history,
            "list_compliance_schedule_run_history",
            tier="read",
        )
        # Writes
        self._add_tool(server, self.create_vm_scan_schedule, "create_vm_scan_schedule", tier="write")
        self._add_tool(server, self.update_vm_scan_schedule, "update_vm_scan_schedule", tier="write")
        self._add_tool(
            server,
            self.create_compliance_scan_schedule,
            "create_compliance_scan_schedule",
            tier="write",
        )
        self._add_tool(
            server,
            self.update_compliance_scan_schedule,
            "update_compliance_scan_schedule",
            tier="write",
        )
        # Destructive (only registered if enable_destructive)
        self._add_tool(
            server, self.delete_vm_scan_schedule, "delete_vm_scan_schedule", tier="destructive"
        )
        self._add_tool(
            server,
            self.delete_compliance_scan_schedule,
            "delete_compliance_scan_schedule",
            tier="destructive",
        )

    # ------------------------------ reads ------------------------------ #
    def list_vm_scan_schedules(
        self,
        id: int | None = None,
        active: bool | None = None,
        show_notifications: bool | None = None,
        scan_type: str | None = None,
        show_cloud_details: bool | None = None,
        client_id: int | None = None,
        client_name: str | None = None,
    ) -> dict[str, Any]:
        """List recurring VM scan schedules in the subscription.

        Args:
            id: Restrict to a single scan schedule ID.
            active: True for active schedules only, False for deactivated only.
                Note: when True, Qualys returns records with active states 1-3.
            show_notifications: Include notification settings in the output.
            scan_type: "certview" or "ec2certview" to restrict to CertView-type
                VM scans, or "perimeter" to restrict to cloud perimeter jobs.
            show_cloud_details: Include cloud details (Provider, Connector,
                Scan Type, Cloud Target) in the output.
            client_id: Consultant-type subscriptions only: client ID filter.
            client_name: Consultant-type subscriptions only: client name
                filter. Mutually exclusive with client_id.

        Returns:
            Parsed SCHEDULE_SCAN_LIST_OUTPUT.
        """
        params = {
            "action": "list",
            "id": id,
            "active": active,
            "show_notifications": show_notifications,
            "scan_type": scan_type,
            "show_cloud_details": show_cloud_details,
            "client_id": client_id,
            "client_name": client_name,
        }
        return self._fo("/api/5.0/fo/schedule/scan/", method="GET", params=params)

    def list_compliance_scan_schedules(
        self,
        id: int | None = None,
        active: bool | None = None,
        show_notifications: bool | None = None,
        show_cloud_details: bool | None = None,
        client_id: int | None = None,
        client_name: str | None = None,
    ) -> dict[str, Any]:
        """List recurring Policy Compliance (PC) scan schedules in the subscription.

        Args:
            id: Restrict to a single scan schedule ID.
            active: True for active schedules only, False for deactivated only.
            show_notifications: Include notification settings in the output.
            show_cloud_details: Include cloud details (Provider, Connector,
                Scan Type, Cloud Target) in the output.
            client_id: Consultant-type subscriptions only: client ID filter.
            client_name: Consultant-type subscriptions only: client name
                filter. Mutually exclusive with client_id.

        Returns:
            Parsed COMPLIANCE_SCHEDULE_SCAN_LIST_OUTPUT.
        """
        params = {
            "action": "list",
            "id": id,
            "active": active,
            "show_notifications": show_notifications,
            "show_cloud_details": show_cloud_details,
            "client_id": client_id,
            "client_name": client_name,
        }
        return self._fo("/api/2.0/fo/schedule/scan/compliance/", method="GET", params=params)

    def list_vm_schedule_run_history(
        self,
        schedule_scan_ids: str,
        schedule_executions_count: int | None = None,
        output_format: str = "xml",
    ) -> dict[str, Any]:
        """List the most recent 'N' scan references for VM scan schedule(s).

        Returns the recent automated scan runs (scan reference, launch time,
        status, duration, option profile, etc.) triggered by each given
        schedule ID — useful for monitoring scheduled VM scans. Does NOT work
        for MAP schedule scan IDs.

        Args:
            schedule_scan_ids: Comma-separated schedule IDs (max 500), e.g.
                "99446,85403,144180".
            schedule_executions_count: How many recent runs to return per
                schedule, 1-50. Defaults to 3 when omitted.
            output_format: "xml" (default) or "json". When "json", the raw
                body is returned under ``{"raw": ...}`` (unparsed).

        Returns:
            Parsed SCHEDULES_RUN_HISTORY when output_format="xml"; otherwise
            ``{"raw": <json text>}``.
        """
        params = {
            "action": "list",
            "schedule_scan_ids": schedule_scan_ids,
            "schedule_executions_count": schedule_executions_count,
            "output_format": output_format,
        }
        parse = output_format == "xml"
        return self._fo(
            "/api/2.0/fo/scan/schedules/runhistory/", method="GET", params=params, parse=parse
        )

    def list_compliance_schedule_run_history(
        self,
        schedule_scan_ids: str,
        schedule_executions_count: int | None = None,
        output_format: str = "xml",
    ) -> dict[str, Any]:
        """List the most recent 'N' scan references for PC scan schedule(s).

        Returns the recent automated scan runs triggered by each given Policy
        Compliance schedule ID. Does NOT work for MAP schedule scan IDs.

        Note: the VM/PC API User Guide documents the exact same endpoint and
        parameters for both VM (p.48) and Compliance (p.61) schedules — there
        is no PC-specific run-history path. This tool exists as a distinct,
        intent-labelled entry point; pass PC schedule IDs in
        ``schedule_scan_ids``.

        Args:
            schedule_scan_ids: Comma-separated PC schedule IDs (max 500).
            schedule_executions_count: How many recent runs to return per
                schedule, 1-50. Defaults to 3 when omitted.
            output_format: "xml" (default) or "json". When "json", the raw
                body is returned under ``{"raw": ...}`` (unparsed).

        Returns:
            Parsed SCHEDULES_RUN_HISTORY when output_format="xml"; otherwise
            ``{"raw": <json text>}``.
        """
        # TODO(verify): the guide lists this same runhistory endpoint under
        # both VM and Compliance sections with identical params; confirm a
        # live PC console accepts PC schedule IDs here (no separate compliance
        # runhistory path is documented).
        params = {
            "action": "list",
            "schedule_scan_ids": schedule_scan_ids,
            "schedule_executions_count": schedule_executions_count,
            "output_format": output_format,
        }
        parse = output_format == "xml"
        return self._fo(
            "/api/2.0/fo/scan/schedules/runhistory/", method="GET", params=params, parse=parse
        )

    # ------------------------------ writes ----------------------------- #
    def create_vm_scan_schedule(
        self,
        scan_title: str,
        active: bool,
        occurrence: str,
        start_hour: int,
        option_id: int | None = None,
        option_title: str | None = None,
        ip: str | None = None,
        asset_group_ids: str | None = None,
        asset_groups: str | None = None,
        exclude_ip_per_scan: str | None = None,
        fqdn: str | None = None,
        iscanner_id: str | None = None,
        iscanner_name: str | None = None,
        priority: int | None = None,
        target_from: str | None = None,
        tag_include_selector: str | None = None,
        tag_exclude_selector: str | None = None,
        tag_set_by: str | None = None,
        tag_set_include: str | None = None,
        tag_set_exclude: str | None = None,
        ip_network_id: int | None = None,
        connector_name: str | None = None,
        connector_uuid: str | None = None,
        ec2_endpoint: str | None = None,
        start_date: str | None = None,
        start_minute: int = 0,
        time_zone_code: str | None = None,
        observe_dst: str | None = None,
        frequency_days: int | None = None,
        frequency_weeks: int | None = None,
        weekdays: str | None = None,
        frequency_months: int | None = None,
        day_of_month: int | None = None,
        day_of_week: int | None = None,
        week_of_month: str | None = None,
        recurrence: int | None = None,
        end_after: int | None = None,
        end_after_mins: int | None = None,
        pause_after_hours: int | None = None,
        pause_after_mins: int | None = None,
        resume_in_days: int | None = None,
        resume_in_hours: int | None = None,
        before_notify: bool | None = None,
        before_notify_unit: str | None = None,
        before_notify_time: int | None = None,
        before_notify_message: str | None = None,
        after_notify: bool | None = None,
        after_notify_message: str | None = None,
        recipient_group_ids: str | None = None,
    ) -> dict[str, Any]:
        """Create a recurring VM scan schedule.

        Provide exactly one option profile selector (option_id or
        option_title), one target (ip, asset_group_ids, asset_groups, fqdn, or
        target_from="tags"), one scanner selector (iscanner_id or
        iscanner_name), and the occurrence-specific fields below.

        Args:
            scan_title: Title for the scheduled scan.
            active: Whether the schedule is active (required).
            occurrence: "daily", "weekly", or "monthly" (required). See the
                matching frequency_* / day_of_* args below for each.
            start_hour: Hour the scan starts, 0-23 (required).
            option_id: Option profile ID to use.
            option_title: Option profile title (alternative to option_id).
            ip: Target IPs/ranges, comma separated.
            asset_group_ids: Comma-separated asset group IDs to scan.
            asset_groups: Comma-separated asset group titles to scan.
            exclude_ip_per_scan: IPs/ranges to exclude, comma separated.
            fqdn: Target FQDNs, comma separated.
            iscanner_id: Scanner appliance ID(s), comma-separated.
            iscanner_name: Scanner appliance name(s), or "External".
            priority: Scan processing priority 0-9 (0 = no priority).
            target_from: "assets" (default) or "tags" for tag-based targeting.
            tag_include_selector: "any" (default) or "all".
            tag_exclude_selector: "any" (default) or "all".
            tag_set_by: "id" (default) or "name".
            tag_set_include: Comma-separated tag IDs/names to include.
            tag_set_exclude: Comma-separated tag IDs/names to exclude.
            ip_network_id: Custom network ID filtering the ip parameter
                (requires Network Support feature).
            connector_name: EC2 connector name (for EC2-targeted schedules).
            connector_uuid: EC2 connector UUID (alternative to connector_name).
            ec2_endpoint: EC2 region endpoint (required with connector_name/
                connector_uuid).
            start_date: Schedule start date, MM/DD/YYYY. Default: today.
            start_minute: Minute the scan starts, 0-59. Default 0.
            time_zone_code: Time zone code in upper case (e.g. "US-CA"). See
                the Time Zone Code API (/msp/time_zone_code_list.php).
            observe_dst: "yes" to observe Daylight Saving Time (only valid for
                time zone codes that support DST).
            frequency_days: Run every N days, 1-365. Required when
                occurrence="daily".
            frequency_weeks: Run every N weeks, 1-52. Required when
                occurrence="weekly".
            weekdays: Comma-separated weekday names (Sunday..Saturday).
                Required when occurrence="weekly".
            frequency_months: Run every N months, 1-12. Required when
                occurrence="monthly".
            day_of_month: Day of month, 1-31, for a monthly schedule that runs
                on a fixed day of the month.
            day_of_week: Day of week, 0 (Sunday) to 6 (Saturday), for a monthly
                schedule that runs on the Nth weekday of the month.
            week_of_month: "first", "second", "third", "fourth", or "last" —
                used together with day_of_week.
            recurrence: Number of times to run before deactivating, 1-99.
            end_after: End the scan after this many hours, 0-119.
            end_after_mins: End the scan after this many minutes, 0-59 (must
                be specified with end_after; minimum 15 when end_after=0).
            pause_after_hours: Pause the scan after this many hours if not
                finished, 0-119.
            pause_after_mins: Pause the scan after this many minutes, 0-59
                (must be specified with pause_after_hours; minimum 15 when
                pause_after_hours=0).
            resume_in_days: Resume a paused scan after this many days, 0-9.
            resume_in_hours: Resume a paused scan after this many hours, 0-23
                (must be specified with resume_in_days).
            before_notify: Send a notification before the scan starts.
            before_notify_unit: "days", "hours", or "minutes" — unit for
                before_notify_time. Required when before_notify=True.
            before_notify_time: How long before the scan to notify (1-31 days,
                1-24 hours, or 5-120 minutes). Required when before_notify=True.
            before_notify_message: Custom message for the before-scan
                notification, up to 4000 chars, no HTML.
            after_notify: Send a notification after the scan finishes.
            after_notify_message: Custom message for the after-scan
                notification, up to 4000 chars, no HTML.
            recipient_group_ids: Comma-separated distribution group IDs to
                notify. Default: only the task owner is notified.

        Returns:
            SIMPLE_RETURN with the new schedule ID, or an error dict.
        """
        data = {
            "action": "create",
            "scan_title": scan_title,
            "active": active,
            "occurrence": occurrence,
            "start_hour": start_hour,
            "option_id": option_id,
            "option_title": option_title,
            "ip": ip,
            "asset_group_ids": asset_group_ids,
            "asset_groups": asset_groups,
            "exclude_ip_per_scan": exclude_ip_per_scan,
            "fqdn": fqdn,
            "iscanner_id": iscanner_id,
            "iscanner_name": iscanner_name,
            "priority": priority,
            "target_from": target_from,
            "tag_include_selector": tag_include_selector,
            "tag_exclude_selector": tag_exclude_selector,
            "tag_set_by": tag_set_by,
            "tag_set_include": tag_set_include,
            "tag_set_exclude": tag_set_exclude,
            "ip_network_id": ip_network_id,
            "connector_name": connector_name,
            "connector_uuid": connector_uuid,
            "ec2_endpoint": ec2_endpoint,
            "start_date": start_date,
            "start_minute": start_minute,
            "time_zone_code": time_zone_code,
            "observe_dst": observe_dst,
            "frequency_days": frequency_days,
            "frequency_weeks": frequency_weeks,
            "weekdays": weekdays,
            "frequency_months": frequency_months,
            "day_of_month": day_of_month,
            "day_of_week": day_of_week,
            "week_of_month": week_of_month,
            "recurrence": recurrence,
            "end_after": end_after,
            "end_after_mins": end_after_mins,
            "pause_after_hours": pause_after_hours,
            "pause_after_mins": pause_after_mins,
            "resume_in_days": resume_in_days,
            "resume_in_hours": resume_in_hours,
            "before_notify": before_notify,
            "before_notify_unit": before_notify_unit,
            "before_notify_time": before_notify_time,
            "before_notify_message": before_notify_message,
            "after_notify": after_notify,
            "after_notify_message": after_notify_message,
            "recipient_group_ids": recipient_group_ids,
        }
        return self._fo("/api/2.0/fo/schedule/scan/", method="POST", data=data)

    def update_vm_scan_schedule(
        self,
        id: int,
        scan_title: str | None = None,
        active: bool | None = None,
        option_id: int | None = None,
        option_title: str | None = None,
        ip: str | None = None,
        asset_group_ids: str | None = None,
        asset_groups: str | None = None,
        exclude_ip_per_scan: str | None = None,
        iscanner_id: str | None = None,
        iscanner_name: str | None = None,
        default_scanner: bool | None = None,
        scanners_in_ag: bool | None = None,
        scanners_in_network: bool | None = None,
        scanners_in_tagset: bool | None = None,
        priority: int | None = None,
        target_from: str | None = None,
        tag_include_selector: str | None = None,
        tag_exclude_selector: str | None = None,
        tag_set_by: str | None = None,
        tag_set_include: str | None = None,
        tag_set_exclude: str | None = None,
        ip_network_id: int | None = None,
        connector_name: str | None = None,
        connector_uuid: str | None = None,
        ec2_endpoint: str | None = None,
        ec2_only_classic: bool | None = None,
        set_start_time: bool | None = None,
        start_date: str | None = None,
        start_hour: int | None = None,
        start_minute: int | None = None,
        time_zone_code: str | None = None,
        observe_dst: str | None = None,
        occurrence: str | None = None,
        frequency_days: int | None = None,
        frequency_weeks: int | None = None,
        weekdays: str | None = None,
        frequency_months: int | None = None,
        day_of_month: int | None = None,
        day_of_week: int | None = None,
        week_of_month: str | None = None,
        recurrence: int | None = None,
        end_after: int | None = None,
        end_after_mins: int | None = None,
        pause_after_hours: int | None = None,
        pause_after_mins: int | None = None,
        resume_in_days: int | None = None,
        resume_in_hours: int | None = None,
        before_notify: bool | None = None,
        before_notify_unit: str | None = None,
        before_notify_time: int | None = None,
        before_notify_message: str | None = None,
        after_notify: bool | None = None,
        after_notify_message: str | None = None,
        recipient_group_ids: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing recurring VM scan schedule.

        Set ``set_start_time=True`` together with start_date/start_hour/
        start_minute/time_zone_code/observe_dst to change the start time; set
        occurrence together with the matching frequency_*/day_of_* fields to
        change recurrence.

        Args:
            id: The scan schedule ID to update (required).
            scan_title: New title for the scheduled scan.
            active: Whether the schedule is active.
            option_id: Option profile ID to use.
            option_title: Option profile title.
            ip: Target IPs/ranges, comma separated.
            asset_group_ids: Comma-separated asset group IDs.
            asset_groups: Comma-separated asset group titles.
            exclude_ip_per_scan: IPs/ranges to exclude, comma separated.
            iscanner_id: Scanner appliance ID(s), comma-separated.
            iscanner_name: Scanner appliance name(s), or "External".
            default_scanner: Use the default scanner in each target asset group.
            scanners_in_ag: Use the scanners defined in each target asset group.
            scanners_in_network: Use all scanners in the target network.
            scanners_in_tagset: Use the scanners in the target tag set.
            priority: Scan processing priority 0-9.
            target_from: "assets" or "tags".
            tag_include_selector: "any" or "all".
            tag_exclude_selector: "any" or "all".
            tag_set_by: "id" or "name".
            tag_set_include: Comma-separated tag IDs/names to include.
            tag_set_exclude: Comma-separated tag IDs/names to exclude.
            ip_network_id: Custom network ID (requires Network Support feature).
            connector_name: EC2 connector name.
            connector_uuid: EC2 connector UUID.
            ec2_endpoint: EC2 region endpoint.
            ec2_only_classic: Restrict EC2 targeting to EC2-Classic instances.
            set_start_time: Set True to apply the start time fields below.
            start_date: New start date, MM/DD/YYYY.
            start_hour: New start hour, 0-23.
            start_minute: New start minute, 0-59.
            time_zone_code: New time zone code, upper case (e.g. "US-CA").
            observe_dst: "yes" to observe Daylight Saving Time.
            occurrence: "daily", "weekly", or "monthly".
            frequency_days: Run every N days, 1-365 (with occurrence="daily").
            frequency_weeks: Run every N weeks, 1-52 (with occurrence="weekly").
            weekdays: Comma-separated weekday names (with occurrence="weekly").
            frequency_months: Run every N months, 1-12 (with occurrence="monthly").
            day_of_month: Day of month, 1-31.
            day_of_week: Day of week, 0 (Sunday) to 6 (Saturday).
            week_of_month: "first", "second", "third", "fourth", or "last".
            recurrence: Number of times to run before deactivating, 1-99.
            end_after: End the scan after this many hours, 0-119.
            end_after_mins: End the scan after this many minutes, 0-59.
            pause_after_hours: Pause the scan after this many hours, 0-119.
            pause_after_mins: Pause the scan after this many minutes, 0-59.
            resume_in_days: Resume a paused scan after this many days, 0-9.
            resume_in_hours: Resume a paused scan after this many hours, 0-23.
            before_notify: Send a notification before the scan starts.
            before_notify_unit: "days", "hours", or "minutes".
            before_notify_time: How long before the scan to notify.
            before_notify_message: Custom before-scan notification message
                (empty string clears the saved message).
            after_notify: Send a notification after the scan finishes.
            after_notify_message: Custom after-scan notification message
                (empty string clears the saved message).
            recipient_group_ids: Comma-separated distribution group IDs
                (empty string clears the saved list).

        Returns:
            SIMPLE_RETURN confirming the update, or an error dict.
        """
        data = {
            "action": "update",
            "id": id,
            "scan_title": scan_title,
            "active": active,
            "option_id": option_id,
            "option_title": option_title,
            "ip": ip,
            "asset_group_ids": asset_group_ids,
            "asset_groups": asset_groups,
            "exclude_ip_per_scan": exclude_ip_per_scan,
            "iscanner_id": iscanner_id,
            "iscanner_name": iscanner_name,
            "default_scanner": default_scanner,
            "scanners_in_ag": scanners_in_ag,
            "scanners_in_network": scanners_in_network,
            "scanners_in_tagset": scanners_in_tagset,
            "priority": priority,
            "target_from": target_from,
            "tag_include_selector": tag_include_selector,
            "tag_exclude_selector": tag_exclude_selector,
            "tag_set_by": tag_set_by,
            "tag_set_include": tag_set_include,
            "tag_set_exclude": tag_set_exclude,
            "ip_network_id": ip_network_id,
            "connector_name": connector_name,
            "connector_uuid": connector_uuid,
            "ec2_endpoint": ec2_endpoint,
            "ec2_only_classic": ec2_only_classic,
            "set_start_time": set_start_time,
            "start_date": start_date,
            "start_hour": start_hour,
            "start_minute": start_minute,
            "time_zone_code": time_zone_code,
            "observe_dst": observe_dst,
            "occurrence": occurrence,
            "frequency_days": frequency_days,
            "frequency_weeks": frequency_weeks,
            "weekdays": weekdays,
            "frequency_months": frequency_months,
            "day_of_month": day_of_month,
            "day_of_week": day_of_week,
            "week_of_month": week_of_month,
            "recurrence": recurrence,
            "end_after": end_after,
            "end_after_mins": end_after_mins,
            "pause_after_hours": pause_after_hours,
            "pause_after_mins": pause_after_mins,
            "resume_in_days": resume_in_days,
            "resume_in_hours": resume_in_hours,
            "before_notify": before_notify,
            "before_notify_unit": before_notify_unit,
            "before_notify_time": before_notify_time,
            "before_notify_message": before_notify_message,
            "after_notify": after_notify,
            "after_notify_message": after_notify_message,
            "recipient_group_ids": recipient_group_ids,
        }
        return self._fo("/api/2.0/fo/schedule/scan/", method="POST", data=data)

    def create_compliance_scan_schedule(
        self,
        scan_title: str,
        active: bool,
        occurrence: str,
        start_hour: int,
        option_id: int | None = None,
        option_title: str | None = None,
        ip: str | None = None,
        asset_group_ids: str | None = None,
        asset_groups: str | None = None,
        exclude_ip_per_scan: str | None = None,
        iscanner_id: str | None = None,
        iscanner_name: str | None = None,
        target_from: str | None = None,
        tag_include_selector: str | None = None,
        tag_exclude_selector: str | None = None,
        tag_set_by: str | None = None,
        tag_set_include: str | None = None,
        tag_set_exclude: str | None = None,
        ip_network_id: int | None = None,
        connector_name: str | None = None,
        ec2_endpoint: str | None = None,
        start_date: str | None = None,
        start_minute: int = 0,
        time_zone_code: str | None = None,
        observe_dst: str | None = None,
        frequency_days: int | None = None,
        frequency_weeks: int | None = None,
        weekdays: str | None = None,
        frequency_months: int | None = None,
        day_of_month: int | None = None,
        day_of_week: int | None = None,
        week_of_month: str | None = None,
        recurrence: int | None = None,
        end_after: int | None = None,
        end_after_mins: int | None = None,
        pause_after_hours: int | None = None,
        pause_after_mins: int | None = None,
        resume_in_days: int | None = None,
        before_notify: bool | None = None,
        before_notify_unit: str | None = None,
        before_notify_time: int | None = None,
        before_notify_message: str | None = None,
        after_notify: bool | None = None,
        after_notify_message: str | None = None,
        recipient_group_ids: str | None = None,
    ) -> dict[str, Any]:
        """Create a recurring Policy Compliance (PC) scan schedule.

        Provide exactly one option profile selector (option_id or
        option_title), one target (ip, asset_group_ids, asset_groups, or
        target_from="tags"), and the occurrence-specific fields below.

        Args:
            scan_title: Title for the scheduled scan (required).
            active: Whether the schedule is active (required).
            occurrence: "daily", "weekly", or "monthly" (required).
            start_hour: Hour the scan starts, 0-23 (required).
            option_id: Option profile ID to use.
            option_title: Option profile title (alternative to option_id).
            ip: Target IPs/ranges, comma separated.
            asset_group_ids: Comma-separated asset group IDs to scan.
            asset_groups: Comma-separated asset group titles to scan.
            exclude_ip_per_scan: IPs/ranges to exclude, comma separated.
            iscanner_id: Scanner appliance ID(s), comma-separated.
            iscanner_name: Scanner appliance name(s), or "External".
            target_from: "assets" (default) or "tags".
            tag_include_selector: "any" (default) or "all".
            tag_exclude_selector: "any" (default) or "all".
            tag_set_by: "id" (default) or "name".
            tag_set_include: Comma-separated tag IDs/names to include.
            tag_set_exclude: Comma-separated tag IDs/names to exclude.
            ip_network_id: Custom network ID filtering the ip parameter.
            connector_name: EC2 connector name (for EC2-targeted schedules).
            ec2_endpoint: EC2 region endpoint (required with connector_name).
            start_date: Schedule start date, MM/DD/YYYY. Default: today.
            start_minute: Minute the scan starts, 0-59. Default 0.
            time_zone_code: Time zone code in upper case (e.g. "US-CA").
            observe_dst: "yes" to observe Daylight Saving Time.
            frequency_days: Run every N days, 1-365 (with occurrence="daily").
            frequency_weeks: Run every N weeks, 1-52 (with occurrence="weekly").
            weekdays: Comma-separated weekday names (with occurrence="weekly").
            frequency_months: Run every N months, 1-12 (with occurrence="monthly").
            day_of_month: Day of month, 1-31.
            day_of_week: Day of week, 0 (Sunday) to 6 (Saturday).
            week_of_month: "first", "second", "third", "fourth", or "last".
            recurrence: Number of times to run before deactivating, 1-99.
            end_after: End the scan after this many hours, 0-119.
            end_after_mins: End the scan after this many minutes, 0-59.
            pause_after_hours: Pause the scan after this many hours, 0-119.
            pause_after_mins: Pause the scan after this many minutes, 0-59.
            resume_in_days: Resume a paused scan after this many days, 0-9.
            before_notify: Send a notification before the scan starts.
            before_notify_unit: "days", "hours", or "minutes".
            before_notify_time: How long before the scan to notify.
            before_notify_message: Custom before-scan notification message.
            after_notify: Send a notification after the scan finishes.
            after_notify_message: Custom after-scan notification message.
            recipient_group_ids: Comma-separated distribution group IDs.

        Returns:
            SIMPLE_RETURN with the new schedule ID, or an error dict.
        """
        data = {
            "action": "create",
            "scan_title": scan_title,
            "active": active,
            "occurrence": occurrence,
            "start_hour": start_hour,
            "option_id": option_id,
            "option_title": option_title,
            "ip": ip,
            "asset_group_ids": asset_group_ids,
            "asset_groups": asset_groups,
            "exclude_ip_per_scan": exclude_ip_per_scan,
            "iscanner_id": iscanner_id,
            "iscanner_name": iscanner_name,
            "target_from": target_from,
            "tag_include_selector": tag_include_selector,
            "tag_exclude_selector": tag_exclude_selector,
            "tag_set_by": tag_set_by,
            "tag_set_include": tag_set_include,
            "tag_set_exclude": tag_set_exclude,
            "ip_network_id": ip_network_id,
            "connector_name": connector_name,
            "ec2_endpoint": ec2_endpoint,
            "start_date": start_date,
            "start_minute": start_minute,
            "time_zone_code": time_zone_code,
            "observe_dst": observe_dst,
            "frequency_days": frequency_days,
            "frequency_weeks": frequency_weeks,
            "weekdays": weekdays,
            "frequency_months": frequency_months,
            "day_of_month": day_of_month,
            "day_of_week": day_of_week,
            "week_of_month": week_of_month,
            "recurrence": recurrence,
            "end_after": end_after,
            "end_after_mins": end_after_mins,
            "pause_after_hours": pause_after_hours,
            "pause_after_mins": pause_after_mins,
            "resume_in_days": resume_in_days,
            "before_notify": before_notify,
            "before_notify_unit": before_notify_unit,
            "before_notify_time": before_notify_time,
            "before_notify_message": before_notify_message,
            "after_notify": after_notify,
            "after_notify_message": after_notify_message,
            "recipient_group_ids": recipient_group_ids,
        }
        return self._fo("/api/2.0/fo/schedule/scan/compliance/", method="POST", data=data)

    def update_compliance_scan_schedule(
        self,
        id: int,
        scan_title: str | None = None,
        active: bool | None = None,
        option_id: int | None = None,
        option_title: str | None = None,
        ip: str | None = None,
        asset_group_ids: str | None = None,
        asset_groups: str | None = None,
        exclude_ip_per_scan: str | None = None,
        iscanner_id: str | None = None,
        iscanner_name: str | None = None,
        default_scanner: bool | None = None,
        scanners_in_ag: bool | None = None,
        scanners_in_network: bool | None = None,
        scanners_in_tagset: bool | None = None,
        target_from: str | None = None,
        tag_include_selector: str | None = None,
        tag_exclude_selector: str | None = None,
        tag_set_by: str | None = None,
        tag_set_include: str | None = None,
        tag_set_exclude: str | None = None,
        ip_network_id: int | None = None,
        set_start_time: bool | None = None,
        start_date: str | None = None,
        start_hour: int | None = None,
        start_minute: int | None = None,
        time_zone_code: str | None = None,
        observe_dst: str | None = None,
        recurrence: int | None = None,
        occurrence: str | None = None,
        frequency_days: int | None = None,
        frequency_weeks: int | None = None,
        weekdays: str | None = None,
        frequency_months: int | None = None,
        day_of_month: int | None = None,
        day_of_week: int | None = None,
        week_of_month: str | None = None,
        end_after: int | None = None,
        end_after_mins: int | None = None,
        pause_after_hours: int | None = None,
        pause_after_mins: int | None = None,
        resume_in_days: int | None = None,
        resume_in_hours: int | None = None,
        before_notify: bool | None = None,
        before_notify_unit: str | None = None,
        before_notify_time: int | None = None,
        before_notify_message: str | None = None,
        after_notify: bool | None = None,
        after_notify_message: str | None = None,
        recipient_group_ids: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing recurring Policy Compliance (PC) scan schedule.

        Set ``set_start_time=True`` together with start_date/start_hour/
        start_minute/time_zone_code/observe_dst to change the start time; set
        occurrence together with the matching frequency_*/day_of_* fields to
        change recurrence.

        Args:
            id: The scan schedule ID to update (required).
            scan_title: New title for the scheduled scan.
            active: Whether the schedule is active.
            option_id: Option profile ID to use.
            option_title: Option profile title.
            ip: Target IPs/ranges, comma separated.
            asset_group_ids: Comma-separated asset group IDs.
            asset_groups: Comma-separated asset group titles.
            exclude_ip_per_scan: IPs/ranges to exclude, comma separated.
            iscanner_id: Scanner appliance ID(s), comma-separated.
            iscanner_name: Scanner appliance name(s), or "External".
            default_scanner: Use the default scanner in each target asset group.
            scanners_in_ag: Use the scanners defined in each target asset group.
            scanners_in_network: Use all scanners in the target network.
            scanners_in_tagset: Use the scanners in the target tag set.
            target_from: "assets" or "tags".
            tag_include_selector: "any" or "all".
            tag_exclude_selector: "any" or "all".
            tag_set_by: "id" or "name".
            tag_set_include: Comma-separated tag IDs/names to include.
            tag_set_exclude: Comma-separated tag IDs/names to exclude.
            ip_network_id: Custom network ID (requires Network Support feature).
            set_start_time: Set True to apply the start time fields below.
            start_date: New start date, MM/DD/YYYY.
            start_hour: New start hour, 0-23.
            start_minute: New start minute, 0-59.
            time_zone_code: New time zone code, upper case (e.g. "US-CA").
            observe_dst: "yes" to observe Daylight Saving Time.
            recurrence: Number of times to run before deactivating, 1-99.
            occurrence: "daily", "weekly", or "monthly".
            frequency_days: Run every N days, 1-365 (with occurrence="daily").
            frequency_weeks: Run every N weeks, 1-52 (with occurrence="weekly").
            weekdays: Comma-separated weekday names (with occurrence="weekly").
            frequency_months: Run every N months, 1-12 (with occurrence="monthly").
            day_of_month: Day of month, 1-31.
            day_of_week: Day of week, 0 (Sunday) to 6 (Saturday).
            week_of_month: "first", "second", "third", "fourth", or "last".
            end_after: End the scan after this many hours, 0-119.
            end_after_mins: End the scan after this many minutes, 0-59.
            pause_after_hours: Pause the scan after this many hours, 0-119.
            pause_after_mins: Pause the scan after this many minutes, 0-59.
            resume_in_days: Resume a paused scan after this many days, 0-9.
            resume_in_hours: Resume a paused scan after this many hours, 0-23.
            before_notify: Send a notification before the scan starts.
            before_notify_unit: "days", "hours", or "minutes".
            before_notify_time: How long before the scan to notify.
            before_notify_message: Custom before-scan notification message.
            after_notify: Send a notification after the scan finishes.
            after_notify_message: Custom after-scan notification message.
            recipient_group_ids: Comma-separated distribution group IDs.

        Returns:
            SIMPLE_RETURN confirming the update, or an error dict.
        """
        data = {
            "action": "update",
            "id": id,
            "scan_title": scan_title,
            "active": active,
            "option_id": option_id,
            "option_title": option_title,
            "ip": ip,
            "asset_group_ids": asset_group_ids,
            "asset_groups": asset_groups,
            "exclude_ip_per_scan": exclude_ip_per_scan,
            "iscanner_id": iscanner_id,
            "iscanner_name": iscanner_name,
            "default_scanner": default_scanner,
            "scanners_in_ag": scanners_in_ag,
            "scanners_in_network": scanners_in_network,
            "scanners_in_tagset": scanners_in_tagset,
            "target_from": target_from,
            "tag_include_selector": tag_include_selector,
            "tag_exclude_selector": tag_exclude_selector,
            "tag_set_by": tag_set_by,
            "tag_set_include": tag_set_include,
            "tag_set_exclude": tag_set_exclude,
            "ip_network_id": ip_network_id,
            "set_start_time": set_start_time,
            "start_date": start_date,
            "start_hour": start_hour,
            "start_minute": start_minute,
            "time_zone_code": time_zone_code,
            "observe_dst": observe_dst,
            "recurrence": recurrence,
            "occurrence": occurrence,
            "frequency_days": frequency_days,
            "frequency_weeks": frequency_weeks,
            "weekdays": weekdays,
            "frequency_months": frequency_months,
            "day_of_month": day_of_month,
            "day_of_week": day_of_week,
            "week_of_month": week_of_month,
            "end_after": end_after,
            "end_after_mins": end_after_mins,
            "pause_after_hours": pause_after_hours,
            "pause_after_mins": pause_after_mins,
            "resume_in_days": resume_in_days,
            "resume_in_hours": resume_in_hours,
            "before_notify": before_notify,
            "before_notify_unit": before_notify_unit,
            "before_notify_time": before_notify_time,
            "before_notify_message": before_notify_message,
            "after_notify": after_notify,
            "after_notify_message": after_notify_message,
            "recipient_group_ids": recipient_group_ids,
        }
        return self._fo("/api/2.0/fo/schedule/scan/compliance/", method="POST", data=data)

    # --------------------------- destructive --------------------------- #
    def delete_vm_scan_schedule(self, id: int, confirm: str | None = None) -> dict[str, Any]:
        """Permanently delete a VM scan schedule. IRREVERSIBLE.

        Gated: requires the console to be started with QUALYS_ENABLE_DESTRUCTIVE
        and the caller to pass confirm=<id>.

        Args:
            id: The scan schedule ID to delete.
            confirm: Must equal ``str(id)`` to proceed.

        Returns:
            SIMPLE_RETURN status, or a confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=str(id))
        if guard:
            return guard
        data = {"action": "delete", "id": id}
        return self._fo("/api/2.0/fo/schedule/scan/", method="POST", data=data)

    def delete_compliance_scan_schedule(self, id: int, confirm: str | None = None) -> dict[str, Any]:
        """Permanently delete a Policy Compliance (PC) scan schedule. IRREVERSIBLE.

        Gated: requires the console to be started with QUALYS_ENABLE_DESTRUCTIVE
        and the caller to pass confirm=<id>.

        Args:
            id: The scan schedule ID to delete.
            confirm: Must equal ``str(id)`` to proceed.

        Returns:
            SIMPLE_RETURN status, or a confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=str(id))
        if guard:
            return guard
        data = {"action": "delete", "id": id}
        return self._fo("/api/2.0/fo/schedule/scan/compliance/", method="POST", data=data)
