"""Compliance Scans module (classic FO API).

Covers Policy Compliance (PC) scans and SCAP scans:
* read  -> list_compliance_scans, list_scap_scans, fetch_compliance_scan_results
* write -> launch_compliance_scan, launch_compliance_scan_on_ec2, manage_compliance_scan
* destructive -> delete_compliance_scan

Endpoints: ``/api/2.0/fo/scan/compliance/`` and ``/api/2.0/fo/scan/scap/``.
Docs: Qualys VM/PC API User Guide — "Compliance Scans".
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class ComplianceScansModule(BaseModule):
    """Launch, monitor, and manage Policy Compliance (PC) and SCAP scans."""

    module_label = "compliance_scans"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(server, self.list_compliance_scans, "list_compliance_scans", tier="read")
        self._add_tool(server, self.list_scap_scans, "list_scap_scans", tier="read")
        self._add_tool(
            server,
            self.fetch_compliance_scan_results,
            "fetch_compliance_scan_results",
            tier="read",
        )
        # Writes (reversible state changes)
        self._add_tool(server, self.launch_compliance_scan, "launch_compliance_scan", tier="write")
        self._add_tool(
            server,
            self.launch_compliance_scan_on_ec2,
            "launch_compliance_scan_on_ec2",
            tier="write",
        )
        self._add_tool(server, self.manage_compliance_scan, "manage_compliance_scan", tier="write")
        # Destructive (only registered if enable_destructive)
        self._add_tool(server, self.delete_compliance_scan, "delete_compliance_scan", tier="destructive")

    # ------------------------------ reads ------------------------------ #
    def list_compliance_scans(
        self,
        scan_id: int | None = None,
        scan_ref: str | None = None,
        state: str | None = None,
        processed: bool | None = None,
        scan_type: str | None = None,
        target: str | None = None,
        user_login: str | None = None,
        launched_after_datetime: str | None = None,
        launched_before_datetime: str | None = None,
        show_ags: bool | None = None,
        show_op: bool | None = None,
        show_status: bool | None = None,
        show_last: bool | None = None,
        client_id: int | None = None,
        client_name: str | None = None,
    ) -> dict[str, Any]:
        """List Policy Compliance scans in the subscription.

        By default lists scans launched in the past 30 days.

        Args:
            scan_id: Restrict to a single compliance scan ID.
            scan_ref: Restrict to a single scan reference (e.g.
                "compliance/1344842952.1340").
            state: Filter by state — Running, Paused, Canceled, Finished,
                Error, Queued, or Loading. Multiple values comma separated.
            processed: Filter by whether results have been processed.
            scan_type: "On-Demand", "Scheduled", or "API".
            target: Target IP address(es)/range(s), comma separated.
            user_login: Restrict to scans launched by this user login.
            launched_after_datetime: ISO datetime lower bound
                (YYYY-MM-DD[THH:MM:SSZ]).
            launched_before_datetime: ISO datetime upper bound (same format).
            show_ags: Include target asset group info in output.
            show_op: Include option profile info in output.
            show_status: Set False to omit scan status (shown by default).
            show_last: Show only the most recent matching scan.
            client_id: Consultant-type subscriptions only: client ID filter.
            client_name: Consultant-type subscriptions only: client name filter.
                Mutually exclusive with client_id.

        Returns:
            Parsed SCAN_LIST_OUTPUT.
        """
        params = {
            "action": "list",
            "scan_id": scan_id,
            "scan_ref": scan_ref,
            "state": state,
            "processed": processed,
            "type": scan_type,
            "target": target,
            "user_login": user_login,
            "launched_after_datetime": launched_after_datetime,
            "launched_before_datetime": launched_before_datetime,
            "show_ags": show_ags,
            "show_op": show_op,
            "show_status": show_status,
            "show_last": show_last,
            "client_id": client_id,
            "client_name": client_name,
        }
        return self._fo("/api/2.0/fo/scan/compliance/", method="GET", params=params)

    def list_scap_scans(
        self,
        scan_id: int | None = None,
        scan_ref: str | None = None,
        state: str | None = None,
        scan_type: str | None = None,
        target: str | None = None,
        user_login: str | None = None,
        launched_after_datetime: str | None = None,
        launched_before_datetime: str | None = None,
        show_ags: bool | None = None,
        show_op: bool | None = None,
        show_status: bool | None = None,
        show_last: bool | None = None,
    ) -> dict[str, Any]:
        """List SCAP scans in the subscription.

        By default lists scans launched in the past 30 days.

        Args:
            scan_id: Restrict to a single compliance scan ID.
            scan_ref: Restrict to a single scan reference (e.g.
                "qscap/1402642816.80342").
            state: Filter by state — Running, Paused, Canceled, Finished,
                Error, Queued, or Loading. Multiple values comma separated.
            scan_type: "On-Demand", "Scheduled", or "API".
            target: Target IP address(es)/range(s), comma separated.
            user_login: Restrict to scans launched by this user login.
            launched_after_datetime: ISO datetime lower bound
                (YYYY-MM-DD[THH:MM:SSZ]).
            launched_before_datetime: ISO datetime upper bound (same format).
            show_ags: Include target asset group info in output.
            show_op: Include option profile info in output.
            show_status: Set False to omit scan status (shown by default).
            show_last: Show only the most recent matching scan.

        Returns:
            Parsed SCAN_LIST_OUTPUT (SCAP scan list, includes POLICY block).
        """
        params = {
            "action": "list",
            "scan_id": scan_id,
            "scan_ref": scan_ref,
            "state": state,
            "type": scan_type,
            "target": target,
            "user_login": user_login,
            "launched_after_datetime": launched_after_datetime,
            "launched_before_datetime": launched_before_datetime,
            "show_ags": show_ags,
            "show_op": show_op,
            "show_status": show_status,
            "show_last": show_last,
        }
        return self._fo("/api/2.0/fo/scan/scap/", method="GET", params=params)

    def fetch_compliance_scan_results(
        self,
        scan_ref: str,
        ips: str | None = None,
        mode: str | None = None,
        output_format: str = "json",
        client_id: int | None = None,
        client_name: str | None = None,
    ) -> dict[str, Any]:
        """Fetch results for a compliance scan with status Finished/Canceled/Paused/Error.

        Args:
            scan_ref: The compliance scan reference (e.g.
                "compliance/1347709693.37303").
            ips: Restrict output to certain IPs/ranges, comma separated.
            mode: "brief" or "extended" detail mode.
            output_format: "csv", "json", "csv_extended", or "json_extended".
            client_id: Consultant-type subscriptions only: client ID.
            client_name: Consultant-type subscriptions only: client name.
                Mutually exclusive with client_id.

        Returns:
            Parsed COMPLIANCE_SCAN_RESULT_OUTPUT, or {"raw": ...} for csv.
        """
        params = {
            "action": "fetch",
            "scan_ref": scan_ref,
            "ips": ips,
            "mode": mode,
            "output_format": output_format,
            "client_id": client_id,
            "client_name": client_name,
        }
        parse = "xml" in output_format.lower()
        return self._fo("/api/2.0/fo/scan/compliance/", method="GET", params=params, parse=parse)

    # ------------------------------ writes ----------------------------- #
    def launch_compliance_scan(
        self,
        scan_title: str,
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
        target_from: str | None = None,
        tag_include_selector: str | None = None,
        tag_exclude_selector: str | None = None,
        tag_set_by: str | None = None,
        tag_set_include: str | None = None,
        tag_set_exclude: str | None = None,
        ip_network_id: int | None = None,
    ) -> dict[str, Any]:
        """Launch a new Policy Compliance scan.

        Provide exactly one option profile selector (option_id or
        option_title) and at least one target (ip, asset_group_ids,
        asset_groups, or target_from="tags" with tag_set_include).

        Args:
            scan_title: Title for the scan.
            option_id: Option profile ID to use.
            option_title: Option profile title (alternative to option_id).
            ip: Target IPs/ranges (e.g. "10.10.25.52,10.10.25.53").
            asset_group_ids: Comma-separated asset group IDs to scan.
            asset_groups: Comma-separated asset group titles to scan.
            exclude_ip_per_scan: IPs/ranges to exclude from this scan only.
            iscanner_id: Scanner appliance ID(s), comma-separated.
            iscanner_name: Scanner appliance name(s), or "External".
            default_scanner: Use the default scanner in each target asset group.
            scanners_in_ag: Use the scanners defined in each target asset group.
            target_from: "assets" (default) or "tags" for tag-based targeting.
            tag_include_selector: "any" (default) or "all" — included-tag match.
            tag_exclude_selector: "any" (default) or "all" — excluded-tag match.
            tag_set_by: "id" (default) or "name" — how tag_set_include/exclude
                identify tags.
            tag_set_include: Comma-separated tag IDs/names to include.
            tag_set_exclude: Comma-separated tag IDs/names to exclude.
            ip_network_id: Custom network ID to filter the ip parameter
                (requires Network Support feature).

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
            "exclude_ip_per_scan": exclude_ip_per_scan,
            "iscanner_id": iscanner_id,
            "iscanner_name": iscanner_name,
            "default_scanner": default_scanner,
            "scanners_in_ag": scanners_in_ag,
            "target_from": target_from,
            "tag_include_selector": tag_include_selector,
            "tag_exclude_selector": tag_exclude_selector,
            "tag_set_by": tag_set_by,
            "tag_set_include": tag_set_include,
            "tag_set_exclude": tag_set_exclude,
            "ip_network_id": ip_network_id,
        }
        return self._fo("/api/2.0/fo/scan/compliance/", method="POST", data=data)

    def launch_compliance_scan_on_ec2(
        self,
        scan_title: str,
        connector_name: str,
        ec2_endpoint: str,
        tag_set_include: str,
        option_id: int | None = None,
        option_title: str | None = None,
        iscanner_id: str | None = None,
        iscanner_name: str | None = None,
        tag_set_by: str | None = None,
        tag_include_selector: str | None = None,
        tag_exclude_selector: str | None = None,
        tag_set_exclude: str | None = None,
    ) -> dict[str, Any]:
        """Launch a compliance scan against Amazon EC2 hosts, selected by tag.

        Requires EC2 Scanning enabled for the account and prior AWS connector
        setup. Unlike VM EC2 scans, tag-based targeting (target_from=tags) is
        required for compliance EC2 scans.

        Args:
            scan_title: Title for the scan.
            connector_name: Name of the configured EC2 connector.
            ec2_endpoint: EC2 region endpoint (e.g. "us-east-1").
            tag_set_include: Comma-separated tag IDs/names to include (required).
            option_id: Option profile ID to use.
            option_title: Option profile title (alternative to option_id).
            iscanner_id: Scanner appliance ID(s), comma-separated.
            iscanner_name: Scanner appliance name(s), comma-separated.
            tag_set_by: "id" (default) or "name" — how tag_set_include/exclude
                identify tags.
            tag_include_selector: "any" (default) or "all" — included-tag match.
            tag_exclude_selector: "any" (default) or "all" — excluded-tag match.
            tag_set_exclude: Comma-separated tag IDs/names to exclude.

        Returns:
            SIMPLE_RETURN with the new scan reference, or an error dict.
        """
        data = {
            "action": "launch",
            "scan_title": scan_title,
            "connector_name": connector_name,
            "ec2_endpoint": ec2_endpoint,
            "target_from": "tags",
            "tag_set_include": tag_set_include,
            "option_id": option_id,
            "option_title": option_title,
            "iscanner_id": iscanner_id,
            "iscanner_name": iscanner_name,
            "tag_set_by": tag_set_by,
            "tag_include_selector": tag_include_selector,
            "tag_exclude_selector": tag_exclude_selector,
            "tag_set_exclude": tag_set_exclude,
        }
        return self._fo("/api/2.0/fo/scan/compliance/", method="POST", data=data)

    def manage_compliance_scan(self, scan_ref: str, operation: str) -> dict[str, Any]:
        """Pause, resume, or cancel a running compliance scan (reversible).

        Args:
            scan_ref: The compliance scan reference to act on (e.g.
                "compliance/1344842952.1340").
            operation: One of "pause", "resume", "cancel".

        Returns:
            SIMPLE_RETURN status, or an error dict.
        """
        operation = operation.lower().strip()
        if operation not in ("pause", "resume", "cancel"):
            return {"error": "operation must be one of: pause, resume, cancel"}
        data = {"action": operation, "scan_ref": scan_ref}
        return self._fo("/api/2.0/fo/scan/compliance/", method="POST", data=data)

    # --------------------------- destructive --------------------------- #
    def delete_compliance_scan(self, scan_ref: str, confirm: str | None = None) -> dict[str, Any]:
        """Permanently delete a compliance scan and its results. IRREVERSIBLE.

        Gated: requires the console to be started with QUALYS_ENABLE_DESTRUCTIVE
        and the caller to pass confirm=<scan_ref>.

        Args:
            scan_ref: The compliance scan reference to delete.
            confirm: Must equal ``scan_ref`` to proceed.

        Returns:
            SIMPLE_RETURN status, or a confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=scan_ref)
        if guard:
            return guard
        data = {"action": "delete", "scan_ref": scan_ref}
        return self._fo("/api/2.0/fo/scan/compliance/", method="POST", data=data)
