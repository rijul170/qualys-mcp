"""Host Assets module (classic FO API) — the core VMDR asset surface.

Covers:
* Host List (``/api/2.0/fo/asset/host/`` action=list) — scanned host inventory.
* Host Update (``/api/2.0/fo/asset/host/`` action=update) — bulk attribute edits.
* Host List Detection (``/api/2.0/fo/asset/host/vm/detection/`` action=list) —
  the per-host vulnerability detection feed. This is the single most important
  VMDR endpoint: it returns NEW/ACTIVE/FIXED/REOPENED detection status, QDS,
  and history for every QID found on every host.

Docs: Qualys VM/PC API User Guide — "Assets" chapter ("Host List", "Host
Update", "Host List Detection").
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class HostAssetsModule(BaseModule):
    """List, update, and pull vulnerability detections for scanned hosts."""

    module_label = "host_assets"

    def register_tools(self, server: FastMCP) -> None:
        self._add_tool(server, self.list_hosts, "list_hosts", tier="read")
        self._add_tool(
            server, self.list_host_detections, "list_host_detections", tier="read"
        )
        self._add_tool(server, self.update_hosts, "update_hosts", tier="write")

    # ------------------------------------------------------------------ #
    # Host List
    # ------------------------------------------------------------------ #
    def list_hosts(
        self,
        ids: str | None = None,
        id_min: int | None = None,
        id_max: int | None = None,
        ips: str | None = None,
        ipv6: str | None = None,
        ag_ids: str | None = None,
        ag_titles: str | None = None,
        network_ids: str | None = None,
        details: str = "Basic",
        os_pattern: str | None = None,
        os_hostname: bool | None = None,
        show_asset_id: bool | None = None,
        truncation_limit: int | None = None,
        compliance_enabled: bool | None = None,
        no_vm_scan_since: str | None = None,
        no_compliance_scan_since: str | None = None,
        vm_scan_since: str | None = None,
        compliance_scan_since: str | None = None,
        vm_processed_before: str | None = None,
        vm_processed_after: str | None = None,
        vm_scan_date_before: str | None = None,
        vm_scan_date_after: str | None = None,
        vm_auth_scan_date_before: str | None = None,
        vm_auth_scan_date_after: str | None = None,
        pc_auth_success_date_before: str | None = None,
        pc_auth_success_date_after: str | None = None,
        scap_scan_since: str | None = None,
        no_scap_scan_since: str | None = None,
        use_tags: bool | None = None,
        tag_set_by: str | None = None,
        tag_include_selector: str | None = None,
        tag_exclude_selector: str | None = None,
        tag_set_include: str | None = None,
        tag_set_exclude: str | None = None,
        show_tags: bool | None = None,
        show_ars: bool | None = None,
        ars_min: int | None = None,
        ars_max: int | None = None,
        show_ars_factors: bool | None = None,
        show_trurisk: bool | None = None,
        trurisk_min: int | None = None,
        trurisk_max: int | None = None,
        show_trurisk_factors: bool | None = None,
        host_metadata: str | None = None,
        host_metadata_fields: str | None = None,
        show_cloud_tags: bool | None = None,
        cloud_tag_fields: str | None = None,
        echo_request: bool | None = None,
    ) -> dict[str, Any]:
        """List scanned hosts in the subscription (host inventory, not detections).

        Args:
            ids: Comma-separated host IDs/ranges (e.g. "190-400,512"). Valid host IDs required.
            id_min: Minimum host ID (inclusive).
            id_max: Maximum host ID (inclusive).
            ips: Comma-separated IPs/ranges (e.g. "10.10.10.1-10.10.10.100").
            ipv6: A valid IPv6 address (comma separated for multiple). Mutually exclusive
                with other target filters when used.
            ag_ids: Comma-separated asset group IDs/ranges (e.g. "386941-386945").
            ag_titles: Comma-separated asset group titles (e.g. "My+Group,Other+Group").
            network_ids: Comma-separated custom network IDs (Network Support feature only).
            details: Level of host info: "Basic" (default), "Basic/AGs", "All",
                "All/AGs", or "None". "/AGs" variants also include asset group info.
            os_pattern: PCRE-compliant, URL-encoded regex to match the OS string.
                Use "%5E%24" to match an empty string.
            os_hostname: Include the OS hostname in the output (default false).
            show_asset_id: Include the numeric asset ID in the output.
            truncation_limit: Max host records per page (default 1000; 0 = no limit —
                use with caution on large subscriptions).
            compliance_enabled: True to list PC-assigned hosts, False for non-PC hosts
                (requires "Manage compliance" permission for sub-accounts).
            no_vm_scan_since: Hosts NOT VM-scanned since this date/time
                (YYYY-MM-DD[THH:MM:SSZ], UTC).
            no_compliance_scan_since: Hosts NOT PC-scanned since this date/time.
            vm_scan_since: Hosts VM-scanned since this date/time.
            compliance_scan_since: Hosts PC-scanned since this date/time.
            vm_processed_before: VM scan results processed before this date/time.
            vm_processed_after: VM scan results processed after this date/time.
            vm_scan_date_before: VM scan end date before this date/time.
            vm_scan_date_after: VM scan end date after this date/time.
            vm_auth_scan_date_before: Successful authenticated VM scan end date before.
            vm_auth_scan_date_after: Successful authenticated VM scan end date after.
            pc_auth_success_date_before: Successful authenticated PC scan end date before.
            pc_auth_success_date_after: Successful authenticated PC scan end date after.
            scap_scan_since: Hosts SCAP-scanned since this date/time.
            no_scap_scan_since: Hosts NOT SCAP-scanned since this date/time.
            use_tags: True to select hosts by asset tags instead of IPs/asset groups.
            tag_set_by: "id" (default) or "name" — how tag_set_include/exclude identify tags.
            tag_include_selector: "any" (default) or "all" — match logic for tag_set_include.
            tag_exclude_selector: "any" (default) or "all" — match logic for tag_set_exclude.
            tag_set_include: Comma-separated tag IDs/names to include (requires use_tags=True).
            tag_set_exclude: Comma-separated tag IDs/names to exclude (requires use_tags=True).
            show_tags: Include each host's asset tags in the output.
            show_ars: Include the Asset Risk Score (ARS) — deprecated in favor of TruRisk.
            ars_min: Minimum ARS (requires show_ars=True).
            ars_max: Maximum ARS (requires show_ars=True).
            show_ars_factors: Include ARS contributing factors.
            show_trurisk: Include the TruRisk score (0-1000: Low 0-499, Medium 500-699,
                High 700-849, Severe 850-1000).
            trurisk_min: Minimum TruRisk score (requires show_trurisk=True).
            trurisk_max: Maximum TruRisk score (requires show_trurisk=True).
            show_trurisk_factors: Include TruRisk contributing factors (per-severity counts).
            host_metadata: Cloud metadata to include: "all", "ec2", "google", or "azure".
            host_metadata_fields: Comma-separated metadata field names to restrict output to
                (requires host_metadata).
            show_cloud_tags: Include cloud provider tags for each host.
            cloud_tag_fields: Comma-separated cloud tag names/name:value pairs to restrict
                output to (requires show_cloud_tags=True).
            echo_request: Echo input parameters back in the output.

        Returns:
            Parsed HOST_LIST_OUTPUT (paginated; a truncation <WARNING> with a
            follow-up URL/id_min is included when more records remain).
        """
        params = {
            "action": "list",
            "ids": ids,
            "id_min": id_min,
            "id_max": id_max,
            "ips": ips,
            "ipv6": ipv6,
            "ag_ids": ag_ids,
            "ag_titles": ag_titles,
            "network_ids": network_ids,
            "details": details,
            "os_pattern": os_pattern,
            "os_hostname": os_hostname,
            "show_asset_id": show_asset_id,
            "truncation_limit": truncation_limit,
            "compliance_enabled": compliance_enabled,
            "no_vm_scan_since": no_vm_scan_since,
            "no_compliance_scan_since": no_compliance_scan_since,
            "vm_scan_since": vm_scan_since,
            "compliance_scan_since": compliance_scan_since,
            "vm_processed_before": vm_processed_before,
            "vm_processed_after": vm_processed_after,
            "vm_scan_date_before": vm_scan_date_before,
            "vm_scan_date_after": vm_scan_date_after,
            "vm_auth_scan_date_before": vm_auth_scan_date_before,
            "vm_auth_scan_date_after": vm_auth_scan_date_after,
            "pc_auth_success_date_before": pc_auth_success_date_before,
            "pc_auth_success_date_after": pc_auth_success_date_after,
            "scap_scan_since": scap_scan_since,
            "no_scap_scan_since": no_scap_scan_since,
            "use_tags": use_tags,
            "tag_set_by": tag_set_by,
            "tag_include_selector": tag_include_selector,
            "tag_exclude_selector": tag_exclude_selector,
            "tag_set_include": tag_set_include,
            "tag_set_exclude": tag_set_exclude,
            "show_tags": show_tags,
            "show_ars": show_ars,
            "ars_min": ars_min,
            "ars_max": ars_max,
            "show_ars_factors": show_ars_factors,
            "show_trurisk": show_trurisk,
            "trurisk_min": trurisk_min,
            "trurisk_max": trurisk_max,
            "show_trurisk_factors": show_trurisk_factors,
            "host_metadata": host_metadata,
            "host_metadata_fields": host_metadata_fields,
            "show_cloud_tags": show_cloud_tags,
            "cloud_tag_fields": cloud_tag_fields,
            "echo_request": echo_request,
        }
        return self._fo("/api/2.0/fo/asset/host/", method="GET", params=params)

    # ------------------------------------------------------------------ #
    # Host List Detection — the crown jewel
    # ------------------------------------------------------------------ #
    def list_host_detections(
        self,
        ids: str | None = None,
        id_min: int | None = None,
        id_max: int | None = None,
        ips: str | None = None,
        ipv6: str | None = None,
        ag_ids: str | None = None,
        ag_titles: str | None = None,
        network_ids: str | None = None,
        network_name: str | None = None,
        status: str | None = None,
        os_pattern: str | None = None,
        compliance_enabled: bool | None = None,
        vm_scan_since: str | None = None,
        no_vm_scan_since: str | None = None,
        max_days_since_last_vm_scan: int | None = None,
        vm_processed_before: str | None = None,
        vm_processed_after: str | None = None,
        vm_scan_date_before: str | None = None,
        vm_scan_date_after: str | None = None,
        vm_auth_scan_date_before: str | None = None,
        vm_auth_scan_date_after: str | None = None,
        qids: str | None = None,
        severities: str | None = None,
        filter_superseded_qids: bool | None = None,
        show_igs: bool | None = None,
        include_search_list_titles: str | None = None,
        exclude_search_list_titles: str | None = None,
        include_search_list_ids: str | None = None,
        exclude_search_list_ids: str | None = None,
        include_vuln_type: str | None = None,
        use_tags: bool | None = None,
        tag_set_by: str | None = None,
        tag_include_selector: str | None = None,
        tag_exclude_selector: str | None = None,
        tag_set_include: str | None = None,
        tag_set_exclude: str | None = None,
        show_tags: bool | None = None,
        show_qds: bool | None = None,
        qds_min: int | None = None,
        qds_max: int | None = None,
        show_qds_factors: bool | None = None,
        host_metadata: str | None = None,
        host_metadata_fields: str | None = None,
        show_cloud_tags: bool | None = None,
        cloud_tag_fields: str | None = None,
        show_results: bool | None = None,
        show_reopened_info: bool | None = None,
        arf_kernel_filter: int | None = None,
        arf_service_filter: int | None = None,
        arf_config_filter: int | None = None,
        detection_updated_since: str | None = None,
        detection_updated_before: str | None = None,
        max_days_since_detection_updated: int | None = None,
        detection_processed_before: str | None = None,
        detection_processed_after: str | None = None,
        detection_last_tested_since: str | None = None,
        detection_last_tested_since_days: int | None = None,
        detection_last_tested_before: str | None = None,
        detection_last_tested_before_days: int | None = None,
        include_ignored: bool | None = None,
        include_disabled: bool | None = None,
        show_host_services: bool | None = None,
        show_asset_id: bool | None = None,
        os_hostname: bool | None = None,
        output_format: str = "xml",
        truncation_limit: int | None = None,
        echo_request: bool | None = None,
    ) -> dict[str, Any]:
        """List hosts with their latest vulnerability detections (the VMDR feed).

        This is the primary source of per-host, per-QID vulnerability status
        (NEW/ACTIVE/FIXED/REOPENED) with full history. Multiple filters combine
        with a logical AND. For large subscriptions, prefer narrow id/ip/asset-group
        filters over unbounded requests to avoid backend performance lag.

        Args:
            ids: Comma-separated host IDs/ranges (e.g. "190-400"). Prefer narrow
                ranges or asset groups over broad ID ranges outside PCP subscriptions.
            id_min: Minimum host ID (inclusive).
            id_max: Maximum host ID (inclusive).
            ips: Comma-separated IPs/ranges (e.g. "10.10.10.1-10.10.10.100").
            ipv6: A valid IPv6 address (comma separated). Mutually exclusive with
                other target filters when used.
            ag_ids: Comma-separated asset group IDs/ranges. Mutually exclusive with ag_titles.
            ag_titles: Comma-separated asset group titles. Mutually exclusive with ag_ids.
            network_ids: Comma-separated custom network IDs (Network Support feature only).
            network_name: Custom network name to display for the matched network ID.
            status: Comma-separated detection statuses to include: "New", "Active",
                "Re-Opened", "Fixed". Default (unspecified) is New,Active,Re-Opened only.
            os_pattern: PCRE-compliant, URL-encoded regex to match the OS string.
            compliance_enabled: True to list PC-assigned hosts scanned/processed,
                False for non-PC hosts.
            vm_scan_since: Hosts scanned and processed since this date/time
                (YYYY-MM-DD[THH:MM:SSZ], UTC). Mutually exclusive with
                max_days_since_last_vm_scan.
            no_vm_scan_since: Hosts NOT scanned/processed since this date/time.
                Mutually exclusive with max_days_since_last_vm_scan.
            max_days_since_last_vm_scan: Hosts scanned/processed within this many
                past days. Mutually exclusive with vm_scan_since/no_vm_scan_since.
            vm_processed_before: VM scan results processed before this date/time.
            vm_processed_after: VM scan results processed after this date/time.
            vm_scan_date_before: VM scan end date before this date/time.
            vm_scan_date_after: VM scan end date after this date/time.
            vm_auth_scan_date_before: Successful authenticated VM scan end date before.
            vm_auth_scan_date_after: Successful authenticated VM scan end date after.
            qids: Comma-separated QIDs/ranges (e.g. "68518-68522").
            severities: Comma-separated severity levels/ranges (e.g. "1-3").
            filter_superseded_qids: True to exclude QIDs superseded by another QID.
            show_igs: Include Information Gathered records alongside vulnerabilities.
                Required (True) when a search-list filter is applied and the list
                contains only Information Gathered QIDs.
            include_search_list_titles: Comma-separated search list titles — only
                include detections whose QID is in one of these lists. Mutually
                exclusive with qids/severities/include_search_list_ids.
            exclude_search_list_titles: Comma-separated search list titles — exclude
                detections whose QID is in one of these lists. Mutually exclusive
                with qids/severities/exclude_search_list_ids.
            include_search_list_ids: Comma-separated search list IDs/ranges to include.
                Mutually exclusive with qids/severities/include_search_list_titles.
            exclude_search_list_ids: Comma-separated search list IDs/ranges to exclude.
                Mutually exclusive with qids/severities/exclude_search_list_titles.
            include_vuln_type: "confirmed" or "potential" — restrict to one vulnerability type.
            use_tags: True to select hosts by asset tags instead of IPs/asset groups.
            tag_set_by: "id" (default) or "name".
            tag_include_selector: "any" (default) or "all".
            tag_exclude_selector: "any" (default) or "all".
            tag_set_include: Comma-separated tag IDs/names to include (requires use_tags=True).
            tag_set_exclude: Comma-separated tag IDs/names to exclude (requires use_tags=True).
            show_tags: Include each host's asset tags in the output.
            show_qds: Include the Qualys Detection Score per detection (1-100: Low
                1-39, Medium 40-69, High 70-89, Critical 90-100).
            qds_min: Minimum QDS (requires show_qds=True).
            qds_max: Maximum QDS (requires show_qds=True).
            show_qds_factors: Include QDS contributing factors per detection.
            host_metadata: Cloud metadata to include: "all", "ec2", "google", or "azure".
            host_metadata_fields: Comma-separated metadata fields to restrict output to.
            show_cloud_tags: Include cloud provider tags for each host.
            cloud_tag_fields: Comma-separated cloud tag names/name:value pairs.
            show_results: False to omit the detection <RESULTS>/Results column (default
                includes them).
            show_reopened_info: Include first/last reopened date and times-reopened.
            arf_kernel_filter: Filter by running-kernel exploitability: 0=tag all kernel
                detections, 1=exclude non-running-kernel, 2=only non-running-kernel,
                3=only running-kernel, 4=tag all (both running/non-running included).
            arf_service_filter: Filter by running-service exploitability (same 0-4 scheme
                as arf_kernel_filter, applied to ports/services).
            arf_config_filter: Filter by exploitable-configuration (same 0-4 scheme,
                applied to host-configuration-dependent vulnerabilities).
            detection_updated_since: Detection status changed on/after this date/time.
                Mutually exclusive with max_days_since_detection_updated.
            detection_updated_before: Detection status changed before this date/time.
            max_days_since_detection_updated: Detection status changed within this many
                past days. Mutually exclusive with detection_updated_since.
            detection_processed_before: Scan results processed before this date/time.
            detection_processed_after: Scan results processed after this date/time.
            detection_last_tested_since: Last tested on/after this date/time. Mutually
                exclusive with detection_last_tested_since_days.
            detection_last_tested_since_days: Last tested within this many past days.
                Mutually exclusive with detection_last_tested_since.
            detection_last_tested_before: Last tested before this date/time. Mutually
                exclusive with detection_last_tested_before_days.
            detection_last_tested_before_days: Last tested more than this many days ago.
                Mutually exclusive with detection_last_tested_before.
            include_ignored: Include QIDs that were ignored during detection.
            include_disabled: Include QIDs that were disabled during detection.
            show_host_services: Include the host's service tag in the output.
            show_asset_id: Include the numeric asset ID in the output.
            os_hostname: Include the OS hostname in the output.
            output_format: "xml" (default), "csv", "csv_no_metadata",
                "csv_no_metadata_ms_excel", or "csv_ms_excel". Qualys only
                accepts lowercase.
            truncation_limit: Max host records per page (default 1000; 0 = no limit —
                use narrow filters when set to 0 to avoid performance issues).
            echo_request: Echo input parameters back in the output.

        Returns:
            Parsed HOST_LIST_VM_DETECTION_OUTPUT (XML) or ``{"raw": ...}`` for CSV
            variants. Truncated results include a <WARNING> with a follow-up URL/id_min.
        """
        params = {
            "action": "list",
            "ids": ids,
            "id_min": id_min,
            "id_max": id_max,
            "ips": ips,
            "ipv6": ipv6,
            "ag_ids": ag_ids,
            "ag_titles": ag_titles,
            "network_ids": network_ids,
            "network_name": network_name,
            "status": status,
            "os_pattern": os_pattern,
            "compliance_enabled": compliance_enabled,
            "vm_scan_since": vm_scan_since,
            "no_vm_scan_since": no_vm_scan_since,
            "max_days_since_last_vm_scan": max_days_since_last_vm_scan,
            "vm_processed_before": vm_processed_before,
            "vm_processed_after": vm_processed_after,
            "vm_scan_date_before": vm_scan_date_before,
            "vm_scan_date_after": vm_scan_date_after,
            "vm_auth_scan_date_before": vm_auth_scan_date_before,
            "vm_auth_scan_date_after": vm_auth_scan_date_after,
            "qids": qids,
            "severities": severities,
            "filter_superseded_qids": filter_superseded_qids,
            "show_igs": show_igs,
            "include_search_list_titles": include_search_list_titles,
            "exclude_search_list_titles": exclude_search_list_titles,
            "include_search_list_ids": include_search_list_ids,
            "exclude_search_list_ids": exclude_search_list_ids,
            "include_vuln_type": include_vuln_type,
            "use_tags": use_tags,
            "tag_set_by": tag_set_by,
            "tag_include_selector": tag_include_selector,
            "tag_exclude_selector": tag_exclude_selector,
            "tag_set_include": tag_set_include,
            "tag_set_exclude": tag_set_exclude,
            "show_tags": show_tags,
            "show_qds": show_qds,
            "qds_min": qds_min,
            "qds_max": qds_max,
            "show_qds_factors": show_qds_factors,
            "host_metadata": host_metadata,
            "host_metadata_fields": host_metadata_fields,
            "show_cloud_tags": show_cloud_tags,
            "cloud_tag_fields": cloud_tag_fields,
            "show_results": show_results,
            "show_reopened_info": show_reopened_info,
            "arf_kernel_filter": arf_kernel_filter,
            "arf_service_filter": arf_service_filter,
            "arf_config_filter": arf_config_filter,
            "detection_updated_since": detection_updated_since,
            "detection_updated_before": detection_updated_before,
            "max_days_since_detection_updated": max_days_since_detection_updated,
            "detection_processed_before": detection_processed_before,
            "detection_processed_after": detection_processed_after,
            "detection_last_tested_since": detection_last_tested_since,
            "detection_last_tested_since_days": detection_last_tested_since_days,
            "detection_last_tested_before": detection_last_tested_before,
            "detection_last_tested_before_days": detection_last_tested_before_days,
            "include_ignored": include_ignored,
            "include_disabled": include_disabled,
            "show_host_services": show_host_services,
            "show_asset_id": show_asset_id,
            "os_hostname": os_hostname,
            "output_format": output_format.lower(),
            "truncation_limit": truncation_limit,
            "echo_request": echo_request,
        }
        parse = output_format.lower() == "xml"
        return self._fo(
            "/api/2.0/fo/asset/host/vm/detection/", method="GET", params=params, parse=parse
        )

    # ------------------------------------------------------------------ #
    # Host Update
    # ------------------------------------------------------------------ #
    def update_hosts(
        self,
        ids: str | None = None,
        ips: str | None = None,
        ag_ids: str | None = None,
        ag_titles: str | None = None,
        network_id: str | None = None,
        network_name: str | None = None,
        tracking_method: str | None = None,
        host_dns: str | None = None,
        host_netbios: str | None = None,
        new_tracking_method: str | None = None,
        new_owner: str | None = None,
        new_ud1: str | None = None,
        new_ud2: str | None = None,
        new_ud3: str | None = None,
        new_comment: str | None = None,
        echo_request: bool | None = None,
    ) -> dict[str, Any]:
        """Bulk-update host attributes (tracking method, owner, UD fields, comments).

        Identify the target hosts using exactly one of these combinations: ``ids``
        alone; ``ips`` (optionally with host_dns/host_netbios/network_id/network_name/
        tracking_method); ``ag_ids`` (optionally with tracking_method); or
        ``ag_titles`` (optionally with tracking_method). New values overwrite the
        existing values on every host matched by the filters.

        Args:
            ids: Comma-separated host IDs (no ranges — single IDs only).
            ips: Comma-separated IPs/ranges to update (e.g. "10.10.30.1-10.10.30.50").
            ag_ids: Comma-separated asset group IDs identifying hosts to update.
            ag_titles: Comma-separated asset group titles identifying hosts to update.
            network_id: Restrict to a custom network ID (Network Support feature only).
            network_name: Restrict to a custom network name (Network Support feature only).
            tracking_method: Filter hosts by current tracking method: "IP", "DNS", "NETBIOS".
            host_dns: DNS hostname to match — use with a single IP in ``ips``.
            host_netbios: NetBIOS hostname to match — use with a single IP in ``ips``.
            new_tracking_method: New tracking method to set: "IP", "DNS", or "NETBIOS".
                Cannot change to/from "EC2" or "AGENT" tracked hosts.
            new_owner: New owner login (must be a Manager, or another role if the IP
                is already in that user's account).
            new_ud1: New value for user-defined field 1 (max 128 ASCII chars).
            new_ud2: New value for user-defined field 2 (max 128 ASCII chars).
            new_ud3: New value for user-defined field 3 (max 128 ASCII chars).
            new_comment: New user-defined comment for the matched host(s).
            echo_request: Echo input parameters back in the output.

        Returns:
            Parsed HOST_UPDATE_OUTPUT confirming the update, or an error dict.
        """
        data = {
            "action": "update",
            "ids": ids,
            "ips": ips,
            "ag_ids": ag_ids,
            "ag_titles": ag_titles,
            "network_id": network_id,
            "network_name": network_name,
            "tracking_method": tracking_method,
            "host_dns": host_dns,
            "host_netbios": host_netbios,
            "new_tracking_method": new_tracking_method,
            "new_owner": new_owner,
            "new_ud1": new_ud1,
            "new_ud2": new_ud2,
            "new_ud3": new_ud3,
            "new_comment": new_comment,
            "echo_request": echo_request,
        }
        return self._fo("/api/2.0/fo/asset/host/", method="POST", data=data)
