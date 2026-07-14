"""VM Scans module (classic FO API) — REFERENCE read/write/destructive module.

Demonstrates all three safety tiers:
* read  -> list_scans, fetch_scan_results, scan_status
* write -> launch_scan, pause/resume/cancel (state changes, reversible)
* destructive -> delete_scan (guarded by _confirm_or_error + enable flag)

Endpoint: ``/api/2.0/fo/scan/``.
Docs: Qualys VM/PC API User Guide — "VM Scans" / "Manage VM Scans".
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class VmScansModule(BaseModule):
    """Launch, monitor, and manage VM scans."""

    module_label = "vm_scans"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(server, self.list_scans, "list_scans", tier="read")
        self._add_tool(server, self.fetch_scan_results, "fetch_scan_results", tier="read")
        self._add_tool(server, self.vm_scan_statistics, "vm_scan_statistics", tier="read")
        self._add_tool(server, self.vm_scan_summary, "vm_scan_summary", tier="read")
        self._add_tool(server, self.scan_summary, "scan_summary", tier="read")
        self._add_tool(server, self.scanner_details, "scanner_details", tier="read")
        self._add_tool(server, self.get_pci_share_status, "get_pci_share_status", tier="read")
        # Writes (reversible state changes)
        self._add_tool(server, self.launch_scan, "launch_scan", tier="write")
        self._add_tool(server, self.launch_scan_on_ec2, "launch_scan_on_ec2", tier="write")
        self._add_tool(server, self.manage_scan, "manage_scan", tier="write")
        self._add_tool(server, self.share_pci_scan, "share_pci_scan", tier="write")
        # Destructive (only registered if enable_destructive)
        self._add_tool(server, self.delete_scan, "delete_scan", tier="destructive")

    # ------------------------------ reads ------------------------------ #
    def list_scans(
        self,
        scan_ref: str | None = None,
        state: str | None = None,
        processed: bool | None = None,
        scan_type: str | None = None,
        launched_after_datetime: str | None = None,
        launched_before_datetime: str | None = None,
        show_ags: bool | None = None,
        show_op: bool | None = None,
    ) -> dict[str, Any]:
        """List VM scans in the subscription.

        Args:
            scan_ref: Restrict to a single scan reference (e.g. "scan/1234567890.12345").
            state: Filter by state — Running, Paused, Canceled, Finished, Error, Queued, Loading.
            processed: Filter by whether results have been processed.
            scan_type: "On-Demand", "Scheduled", or "API".
            launched_after_datetime: ISO datetime lower bound (YYYY-MM-DDTHH:MM:SSZ).
            launched_before_datetime: ISO datetime upper bound.
            show_ags: Include target asset groups in output.
            show_op: Include option profile in output.

        Returns:
            Parsed SCAN_LIST_OUTPUT.
        """
        params = {
            "action": "list",
            "scan_ref": scan_ref,
            "state": state,
            "processed": processed,
            "scan_type": scan_type,
            "launched_after_datetime": launched_after_datetime,
            "launched_before_datetime": launched_before_datetime,
            "show_ags": show_ags,
            "show_op": show_op,
        }
        return self._fo("/api/2.0/fo/scan/", method="GET", params=params)

    def fetch_scan_results(
        self,
        scan_ref: str,
        output_format: str = "json",
        mode: str | None = None,
    ) -> dict[str, Any]:
        """Fetch results for a finished scan.

        Args:
            scan_ref: The scan reference to fetch (e.g. "scan/1234567890.12345").
            output_format: "json", "csv", "xml", or "json_extended".
            mode: "brief" or "extended" detail mode.

        Returns:
            Parsed scan results (or {"raw": ...} for csv).
        """
        params = {
            "action": "fetch",
            "scan_ref": scan_ref,
            "output_format": output_format,
            "mode": mode,
        }
        parse = output_format in ("xml",)
        return self._fo("/api/2.0/fo/scan/", method="GET", params=params, parse=parse)

    def vm_scan_statistics(self) -> dict[str, Any]:
        """List unprocessed VM scans and the VM recrypt processing backlog.

        Reports the total number of unprocessed scans plus per-scan and
        per-task backlog details for hosts still waiting to be processed.

        Returns:
            Parsed TASK_PROCESSING output (UNPROCESSED_SCANS, VM_RECRYPT_BACKLOG,
            VM_RECRYPT_BACKLOG_BY_SCAN, VM_RECRYPT_BACKLOG_BY_TASK).
        """
        params = {"action": "list"}
        return self._fo("/api/2.0/fo/scan/stats/", method="GET", params=params)

    def vm_scan_summary(
        self,
        output_format: str = "xml",
        scan_reference: str | None = None,
        scan_datetime_since: str | None = None,
        scan_datetime_until: str | None = None,
        include_scan_input: bool | None = None,
        include_scan_details: bool | None = None,
        include_hosts_summary: bool | None = None,
        include_detections_summary: bool | None = None,
        include_hosts_summary_categories: str | None = None,
    ) -> dict[str, Any]:
        """Identify hosts scanned/not-scanned and why, for one or more VM scans.

        Improved alternative to ``scan_summary``. Either ``scan_reference`` or
        ``scan_datetime_since`` must be provided (mutually exclusive).

        Args:
            output_format: Only "xml" is currently supported by Qualys.
            scan_reference: A single scan reference (e.g. "scan/987654321.98765").
                Cannot be combined with scan_datetime_since/scan_datetime_until.
            scan_datetime_since: Include scans started since this datetime, RFC
                3339 UTC (YYYY-MM-DDTHH:MM:SSZ), e.g. "2020-10-01T09:30:48Z".
            scan_datetime_until: Include scans started up to this datetime
                (same format). Requires scan_datetime_since to also be set.
            include_scan_input: Include the SCAN_INPUT block (title, user,
                target, network, option profile). Default True server-side.
            include_scan_details: Include the SCAN_DETAILS block (status,
                launch datetime, duration). Default True server-side.
            include_hosts_summary: Include the HOSTS block under SCAN_RESULTS.
                Default True server-side.
            include_detections_summary: Include the DETECTIONS block under
                SCAN_RESULTS. Default True server-side.
            include_hosts_summary_categories: Comma-separated host summary
                categories to include: scanned, excluded, cancelled,
                unresolved, duplicate, not_vulnerable, dead, aborted, blocked,
                failed_slice, exceeded_scan_duration. Default: all categories.

        Returns:
            Parsed SCAN_SUMMARY_OUTPUT (SCAN_SUMMARY_LIST of SCAN_SUMMARY).
        """
        params = {
            "action": "list",
            "output_format": output_format,
            "scan_reference": scan_reference,
            "scan_datetime_since": scan_datetime_since,
            "scan_datetime_until": scan_datetime_until,
            "include_scan_input": include_scan_input,
            "include_scan_details": include_scan_details,
            "include_hosts_summary": include_hosts_summary,
            "include_detections_summary": include_detections_summary,
            "include_hosts_summary_categories": include_hosts_summary_categories,
        }
        return self._fo("/api/2.0/fo/scan/vm/summary/", method="GET", params=params)

    def scan_summary(
        self,
        scan_date_since: str,
        scan_date_to: str | None = None,
        output_format: str = "xml",
        tracking_method: str | None = None,
        include_dead: bool | None = None,
        include_excluded: bool | None = None,
        include_unresolved: bool | None = None,
        include_cancelled: bool | None = None,
        include_notvuln: bool | None = None,
        include_blocked: bool | None = None,
        include_duplicate: bool | None = None,
        include_aborted: bool | None = None,
    ) -> dict[str, Any]:
        """Original VM Scan Summary API — hosts not scanned and why.

        Superseded by ``vm_scan_summary`` (more filters, richer output) but
        still supported. Dead hosts are included by default; other categories
        are excluded by default.

        Args:
            scan_date_since: Include scans started since this date, YYYY-MM-DD.
                Must be <= today.
            scan_date_to: Include scans started up to this date, YYYY-MM-DD.
                Must be >= scan_date_since and <= today.
            output_format: "xml" (default), "csv", or "json".
            tracking_method: Restrict to hosts tracked by "IP", "DNS", or
                "NETBIOS". Default: any tracking method.
            include_dead: Set False to exclude dead hosts (included by default).
            include_excluded: Include hosts excluded from the scan.
            include_unresolved: Include hosts whose hostname could not be resolved.
            include_cancelled: Include hosts from cancelled scans.
            include_notvuln: Include hosts found not vulnerable during discovery.
            include_blocked: Include hosts blocked from scanning.
            include_duplicate: Include duplicate hosts within a scan slice.
            include_aborted: Include hosts from abruptly discontinued scans.

        Returns:
            Parsed SCAN_SUMMARY_OUTPUT (SCAN_SUMMARY_LIST of HOST_SUMMARY
            entries by category/tracking method), or {"raw": ...} for csv.
        """
        params = {
            "action": "list",
            "scan_date_since": scan_date_since,
            "scan_date_to": scan_date_to,
            "output_format": output_format,
            "tracking_method": tracking_method,
            "include_dead": include_dead,
            "include_excluded": include_excluded,
            "include_unresolved": include_unresolved,
            "include_cancelled": include_cancelled,
            "include_notvuln": include_notvuln,
            "include_blocked": include_blocked,
            "include_duplicate": include_duplicate,
            "include_aborted": include_aborted,
        }
        parse = output_format.lower() == "xml"
        return self._fo("/api/2.0/fo/scan/summary/", method="GET", params=params, parse=parse)

    def scanner_details(
        self,
        ips: str,
        scan_date_since: str,
        scan_date_to: str | None = None,
        output_format: str = "xml",
    ) -> dict[str, Any]:
        """Identify which scanner appliance/external scanner scanned given IPs.

        Useful when a pool of scanners was used and it's unclear which one
        scanned a particular host. Vulnerability scans only.

        Args:
            ips: IP addresses/ranges to look up (e.g. "10.10.10.2-10.10.10.7,
                10.10.10.10"). Multiple entries comma separated.
            scan_date_since: Include scans started since this date, YYYY-MM-DD.
                Must be <= today.
            scan_date_to: Include scans started up to this date, YYYY-MM-DD.
                Must be >= scan_date_since and <= today.
            output_format: Only "xml" is currently supported. Qualys only
                accepts lowercase.

        Returns:
            Parsed IP_SCANNERS_LIST_OUTPUT (per-IP scanner identifier, type,
            and software versions).
        """
        params = {
            "action": "list",
            "ips": ips,
            "scan_date_since": scan_date_since,
            "scan_date_to": scan_date_to,
            "output_format": output_format.lower(),
        }
        return self._fo("/api/2.0/fo/scan/scanner/", method="GET", params=params)

    def get_pci_share_status(self, scan_ref: str, merchant_username: str) -> dict[str, Any]:
        """Get the export status of a PCI scan previously shared with a merchant account.

        Args:
            scan_ref: The scan reference of the shared scan (e.g.
                "scan/1531755831.21639").
            merchant_username: Username of the PCI Merchant account the scan
                was shared with.

        Returns:
            Parsed PCI_SCAN_SHARE_STATUS (STATUS: Queued, In Progress,
            Finished, or Error).
        """
        params = {"action": "status", "scan_ref": scan_ref, "merchant_username": merchant_username}
        return self._fo("/api/2.0/fo/scan/pci/", method="GET", params=params)

    # ------------------------------ writes ----------------------------- #
    def launch_scan(
        self,
        scan_title: str,
        option_id: int | None = None,
        option_title: str | None = None,
        ip: str | None = None,
        asset_group_ids: str | None = None,
        asset_groups: str | None = None,
        iscanner_name: str | None = None,
        default_scanner: bool | None = None,
        priority: int | None = None,
        fqdn: str | None = None,
    ) -> dict[str, Any]:
        """Launch a new VM scan.

        Provide exactly one option profile selector (option_id or option_title)
        and at least one target (ip, asset_group_ids, asset_groups, or fqdn).

        Args:
            scan_title: Title for the scan.
            option_id: Option profile ID to use.
            option_title: Option profile title to use (alternative to option_id).
            ip: Target IPs/ranges (e.g. "10.0.0.1-10.0.0.10,10.0.1.0/24").
            asset_group_ids: Comma-separated asset group IDs to scan.
            asset_groups: Comma-separated asset group titles to scan.
            iscanner_name: Scanner appliance name(s) to use.
            default_scanner: Use the default scanner for the target.
            priority: Scan priority 0-9 (0 = no priority).
            fqdn: Target FQDNs (comma-separated).

        Returns:
            SIMPLE_RETURN with the new scan reference, or an error dict.
        """
        data = {
            "action": "launch",
            "scan_title": scan_title,
            "option_id": option_id,
            "option_title": option_title,
            "ip": ip,
            "asset_group_ids": asset_group_ids,
            "asset_groups": asset_groups,
            "iscanner_name": iscanner_name,
            "default_scanner": default_scanner,
            "priority": priority,
            "fqdn": fqdn,
        }
        return self._fo("/api/2.0/fo/scan/", method="POST", data=data)

    def launch_scan_on_ec2(
        self,
        scan_title: str,
        connector_name: str,
        ec2_endpoint: str,
        option_id: int | None = None,
        option_title: str | None = None,
        iscanner_id: str | None = None,
        iscanner_name: str | None = None,
        ec2_instance_ids: str | None = None,
        target_from: str | None = None,
        tag_set_by: str | None = None,
        tag_set_include: str | None = None,
        tag_set_exclude: str | None = None,
        tag_include_selector: str | None = None,
        tag_exclude_selector: str | None = None,
        priority: int | None = None,
    ) -> dict[str, Any]:
        """Launch a VM scan against Amazon EC2 hosts.

        Requires EC2 Scanning enabled for the account and prior AWS connector
        setup. You may target instances via ``ec2_instance_ids`` and/or via
        tags (``target_from="tags"`` with the tag_set_* parameters).

        Args:
            scan_title: Title for the scan.
            connector_name: Name of the configured EC2 connector.
            ec2_endpoint: EC2 region endpoint (e.g. "us-east-1").
            option_id: Option profile ID to use.
            option_title: Option profile title (alternative to option_id).
            iscanner_id: Scanner appliance ID(s), comma-separated.
            iscanner_name: Scanner appliance name(s), comma-separated (e.g.
                "EC2-1" or "External").
            ec2_instance_ids: Comma-separated EC2 instance IDs to scan (max 10).
                May be combined with tag-based targeting.
            target_from: Set to "tags" to select EC2 hosts by tag.
            tag_set_by: "id" or "name" — how tag_set_include/exclude identify
                tags. Only valid when target_from="tags".
            tag_set_include: Comma-separated tag IDs/names to include
                (required when target_from="tags").
            tag_set_exclude: Comma-separated tag IDs/names to exclude.
            tag_include_selector: "any" or "all" — match logic for included tags.
            tag_exclude_selector: "any" or "all" — match logic for excluded tags.
            priority: Scan processing priority 0-9 (0 = no priority).

        Returns:
            SIMPLE_RETURN with the new scan reference (and a NOTIFICATION
            listing any skipped instance IDs), or an error dict.
        """
        data = {
            "action": "launch",
            "scan_title": scan_title,
            "connector_name": connector_name,
            "ec2_endpoint": ec2_endpoint,
            "option_id": option_id,
            "option_title": option_title,
            "iscanner_id": iscanner_id,
            "iscanner_name": iscanner_name,
            "ec2_instance_ids": ec2_instance_ids,
            "target_from": target_from,
            "tag_set_by": tag_set_by,
            "tag_set_include": tag_set_include,
            "tag_set_exclude": tag_set_exclude,
            "tag_include_selector": tag_include_selector,
            "tag_exclude_selector": tag_exclude_selector,
            "priority": priority,
        }
        return self._fo("/api/2.0/fo/scan/", method="POST", data=data)

    def manage_scan(self, scan_ref: str, operation: str) -> dict[str, Any]:
        """Pause, resume, or cancel a running scan (reversible operations).

        Args:
            scan_ref: The scan reference to act on.
            operation: One of "pause", "resume", "cancel".

        Returns:
            SIMPLE_RETURN status, or an error dict.
        """
        operation = operation.lower().strip()
        if operation not in ("pause", "resume", "cancel"):
            return {"error": "operation must be one of: pause, resume, cancel"}
        data = {"action": operation, "scan_ref": scan_ref}
        return self._fo("/api/2.0/fo/scan/", method="POST", data=data)

    def share_pci_scan(
        self, scan_ref: str, merchant_username: str, echo_request: bool | None = None
    ) -> dict[str, Any]:
        """Export (share) a finished PCI scan to a PCI Merchant account.

        A PCI scan can be shared with a given merchant account only once. The
        target merchant account must already have a PCI account link defined
        (via the Qualys UI) with the API user's account.

        Args:
            scan_ref: Scan reference of a finished PCI scan (status "Finished").
            merchant_username: Username of the target PCI Merchant account.
            echo_request: Echo the input parameters in the XML output.

        Returns:
            SIMPLE_RETURN confirming the share request was queued, or an
            error dict (e.g. if already shared).
        """
        data = {
            "action": "share",
            "scan_ref": scan_ref,
            "merchant_username": merchant_username,
            "echo_request": echo_request,
        }
        return self._fo("/api/2.0/fo/scan/pci/", method="POST", data=data)

    # --------------------------- destructive --------------------------- #
    def delete_scan(self, scan_ref: str, confirm: str | None = None) -> dict[str, Any]:
        """Permanently delete a scan and its results. IRREVERSIBLE.

        Gated: requires the console to be started with QUALYS_ENABLE_DESTRUCTIVE
        and the caller to pass confirm=<scan_ref>.

        Args:
            scan_ref: The scan reference to delete.
            confirm: Must equal ``scan_ref`` to proceed.

        Returns:
            SIMPLE_RETURN status, or a confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=scan_ref)
        if guard:
            return guard
        data = {"action": "delete", "scan_ref": scan_ref}
        return self._fo("/api/2.0/fo/scan/", method="POST", data=data)
