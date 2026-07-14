"""Reports module (classic FO API) — Report Share reporting.

Covers launching, monitoring, downloading, and deleting reports and
scorecards, plus scheduled-report control and the ad hoc asset search report.

Endpoints:
* ``/api/2.0/fo/report/`` (list, launch, cancel, fetch, delete)
* ``/api/2.0/fo/report/scorecard/`` (launch scorecard)
* ``/api/2.0/fo/schedule/report/`` (scheduled reports list, launch_now)
* ``/api/2.0/fo/report/asset/`` (asset search report)

Docs: Qualys VM/PC API User Guide — "Reports".
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class ReportsModule(BaseModule):
    """Launch, monitor, download, and manage Qualys reports and scorecards."""

    module_label = "reports"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(server, self.list_reports, "list_reports", tier="read")
        self._add_tool(server, self.download_report, "download_report", tier="read")
        self._add_tool(server, self.scheduled_reports_list, "scheduled_reports_list", tier="read")
        # Writes
        self._add_tool(server, self.launch_report, "launch_report", tier="write")
        self._add_tool(server, self.launch_scorecard, "launch_scorecard", tier="write")
        self._add_tool(server, self.cancel_report, "cancel_report", tier="write")
        self._add_tool(
            server, self.launch_scheduled_report, "launch_scheduled_report", tier="write"
        )
        self._add_tool(server, self.asset_search_report, "asset_search_report", tier="write")
        # Destructive
        self._add_tool(server, self.delete_report, "delete_report", tier="destructive")

    # ------------------------------ reads ------------------------------ #
    def list_reports(
        self,
        id: int | None = None,
        state: str | None = None,
        user_login: str | None = None,
        expires_before_datetime: str | None = None,
        client_id: str | None = None,
        client_name: str | None = None,
    ) -> dict[str, Any]:
        """List reports in the user's Report Share account.

        Args:
            id: Restrict to a single report ID stored in Report Share.
            state: Filter by report state — "Running", "Finished", "Submitted",
                "Canceled", or "Errors". All states are included by default.
            user_login: Restrict to reports launched by this user login ID.
            expires_before_datetime: ISO datetime (YYYY-MM-DD[THH:MM:SSZ]) —
                only reports expiring before this date/time are included.
            client_id: Consultant-type subscriptions only — id of the client.
                Mutually exclusive with client_name.
            client_name: Consultant-type subscriptions only — name of the
                client. Mutually exclusive with client_id.

        Returns:
            Parsed REPORT_LIST_OUTPUT.
        """
        params = {
            "action": "list",
            "id": id,
            "state": state,
            "user_login": user_login,
            "expires_before_datetime": expires_before_datetime,
            "client_id": client_id,
            "client_name": client_name,
        }
        return self._fo("/api/2.0/fo/report/", method="GET", params=params)

    def download_report(self, id: int, output_format: str | None = None) -> dict[str, Any]:
        """Download a finished saved report from Report Share.

        Args:
            id: Report ID of a saved report in the "Finished" state (see
                ``list_reports``).
            output_format: The format the report was launched with, if known.
                Pass "xml" to have the response body parsed into a dict. Any
                other value (or omission) returns the raw body — required for
                pdf/html(zip)/docx/csv/other binary reports.

        Returns:
            Parsed report dict when output_format="xml"; otherwise
            ``{"raw": <response body>}``.
        """
        params = {"action": "fetch", "id": id}
        parse = output_format == "xml"
        return self._fo("/api/2.0/fo/report/", method="GET", params=params, parse=parse)

    def scheduled_reports_list(
        self, id: int | None = None, is_active: bool | None = None
    ) -> dict[str, Any]:
        """List scheduled reports in the user's account.

        Args:
            id: Restrict to a single scheduled report ID.
            is_active: True to list active scheduled reports only, False for
                inactive only. Both are listed by default.

        Returns:
            Parsed scheduled report list output.
        """
        params = {"action": "list", "id": id, "is_active": is_active}
        return self._fo("/api/2.0/fo/schedule/report/", method="GET", params=params)

    # ------------------------------ writes ----------------------------- #
    def launch_report(
        self,
        template_id: int,
        output_format: str,
        report_title: str | None = None,
        hide_header: bool | None = None,
        pdf_password: str | None = None,
        recipient_group: str | None = None,
        recipient_group_id: str | None = None,
        report_type: str | None = None,
        domain: str | None = None,
        ip_restriction: str | None = None,
        report_refs: str | None = None,
        ips: str | None = None,
        asset_group_ids: str | None = None,
        ips_network_id: str | None = None,
        fqdns: str | None = None,
        assignee_type: str | None = None,
        policy_id: int | None = None,
        host_id: int | None = None,
        instance_string: str | None = None,
        use_tags: bool | None = None,
        tag_include_selector: str | None = None,
        tag_exclude_selector: str | None = None,
        tag_set_by: str | None = None,
        tag_set_include: str | None = None,
        tag_set_exclude: str | None = None,
    ) -> dict[str, Any]:
        """Launch a report in Report Share and return its new report ID.

        Provide exactly one target selector appropriate to the report type:
        report_refs (map / manual scan / PCI compliance), ips/asset_group_ids
        (scan host-based / patch / remediation / compliance), policy_id (+
        optional ips/asset_group_ids/host_id+instance_string) for a compliance
        policy report, or asset tags (use_tags=True plus tag_set_include).

        Args:
            template_id: Report template ID to launch (see
                ``report_templates.list_report_templates``).
            output_format: Output format. Valid per report type — map: pdf,
                html, xml, csv; scan: pdf, html, xml, csv, docx; remediation:
                pdf, html, csv; compliance (non-PCI): pdf, html; PCI
                compliance: pdf, html; patch: pdf, online, xml, csv;
                compliance policy: pdf, html, xml, csv.
            report_title: User-defined title (max 128 chars). Ignored for PCI
                compliance reports (title is fixed by Qualys).
            hide_header: CSV format only — omit the header block when True.
            pdf_password: Secure PDF distribution password (Manager/Unit
                Manager only; 8-32 chars, alpha+numeric, must differ from the
                user's own account password).
            recipient_group: Comma-separated distribution group names for
                secure PDF distribution. Requires pdf_password. Mutually
                exclusive with recipient_group_id.
            recipient_group_id: Comma-separated distribution group IDs for
                secure PDF distribution. Requires pdf_password. Mutually
                exclusive with recipient_group.
            report_type: "Map", "Scan", "Remediation", "Compliance", or
                "Policy".
            domain: Map report only — target domain (no "www." prefix), or
                "none" with ip_restriction set.
            ip_restriction: Map / manual-scan report only — restrict report
                content to these IPs/ranges (comma-separated).
            report_refs: Map ("map/<id>", up to 2 comma-separated) / manual
                scan report ("scan/<id>", comma-separated) / PCI compliance
                report (single "scan/<id>" from a scan run with the PCI
                Options profile) target reference(s).
            ips: Comma-separated IPs/ranges to target for scan (host-based) /
                patch / remediation / compliance / policy reports.
            asset_group_ids: Comma-separated asset group IDs to target for
                scan (host-based) / patch / remediation / compliance / policy
                reports.
            ips_network_id: Network Support feature only — network ID
                restricting `ips` for a host-based scan report. "0" (default)
                is the Global Default Network.
            fqdns: Comma-separated target FQDNs for a host-based vulnerability
                scan report.
            assignee_type: Remediation report only — "User" (default; tickets
                assigned to the caller) or "All" (all tickets in the account).
            policy_id: Required for a compliance policy report — the policy ID
                to report on.
            host_id: Compliance policy report only — restrict output to one
                host instance. Must be paired with instance_string.
            instance_string: Compliance policy report only — the instance on
                the selected host, e.g. "os" or "oracle10:1:1521:ora10204u".
                Must be paired with host_id.
            use_tags: Set True to select the report target via asset tags
                instead of ips/asset_group_ids.
            tag_include_selector: "any" (default) or "all" — how
                tag_set_include tags combine.
            tag_exclude_selector: "any" (default) or "all" — how
                tag_set_exclude tags combine.
            tag_set_by: "id" (default) or "name" — whether tag_set_include/
                tag_set_exclude are given as IDs or names.
            tag_set_include: Comma-separated tag IDs/names identifying hosts
                to include.
            tag_set_exclude: Comma-separated tag IDs/names identifying hosts
                to exclude.

        Returns:
            SIMPLE_RETURN with the new report ID, or an error dict.
        """
        data = {
            "action": "launch",
            "template_id": template_id,
            "output_format": output_format,
            "report_title": report_title,
            "hide_header": hide_header,
            "pdf_password": pdf_password,
            "recipient_group": recipient_group,
            "recipient_group_id": recipient_group_id,
            "report_type": report_type,
            "domain": domain,
            "ip_restriction": ip_restriction,
            "report_refs": report_refs,
            "ips": ips,
            "asset_group_ids": asset_group_ids,
            "ips_network_id": ips_network_id,
            "fqdns": fqdns,
            "assignee_type": assignee_type,
            "policy_id": policy_id,
            "host_id": host_id,
            "instance_string": instance_string,
            "use_tags": use_tags,
            "tag_include_selector": tag_include_selector,
            "tag_exclude_selector": tag_exclude_selector,
            "tag_set_by": tag_set_by,
            "tag_set_include": tag_set_include,
            "tag_set_exclude": tag_set_exclude,
        }
        return self._fo("/api/2.0/fo/report/", method="POST", data=data)

    def launch_scorecard(
        self,
        name: str,
        output_format: str,
        report_title: str | None = None,
        hide_header: bool | None = None,
        pdf_password: str | None = None,
        recipient_group: str | None = None,
        recipient_group_id: str | None = None,
        source: str | None = None,
        asset_groups: str | None = None,
        all_asset_groups: bool | None = None,
        business_unit: str | None = None,
        division: str | None = None,
        function: str | None = None,
        location: str | None = None,
        patch_qids: str | None = None,
        missing_qids: str | None = None,
    ) -> dict[str, Any]:
        """Launch a vulnerability scorecard report in Report Share.

        Compliance and WAS scorecards cannot be launched via this API.

        Args:
            name: Scorecard name — a service-provided name ("Asset Group
                Vulnerability Report", "Ignored Vulnerabilities Report",
                "Most Prevalent Vulnerabilities Report", "Most Vulnerable
                Hosts Report", "Patch Report") or a user-created scorecard
                name.
            output_format: "pdf", "html" (zip file), "xml", or "csv".
            report_title: User-defined title (max 128 chars); defaults to the
                scorecard name.
            hide_header: CSV format only — omit the header block when True.
            pdf_password: Secure PDF distribution password (Manager/Unit
                Manager only, max 32 chars, must differ from the user's own
                account password).
            recipient_group: Comma-separated distribution group names for
                secure PDF distribution. Requires pdf_password. Mutually
                exclusive with recipient_group_id.
            recipient_group_id: Comma-separated distribution group IDs for
                secure PDF distribution. Requires pdf_password. Mutually
                exclusive with recipient_group.
            source: Source of the report's asset groups — "asset_groups" or
                "business_unit". Required for a service-provided scorecard.
            asset_groups: Comma-separated asset group titles (source=
                asset_groups only). Mutually exclusive with all_asset_groups.
            all_asset_groups: Set True to select all asset groups in the
                account (source=asset_groups only). Mutually exclusive with
                asset_groups.
            business_unit: Business unit title containing the source asset
                groups (source=business_unit; Manager only), or "Unassigned".
            division: Business info tag identifying a division
                (source=business_unit only).
            function: Business info tag identifying a business function
                (source=business_unit only).
            location: Business info tag identifying a location
                (source=business_unit only).
            patch_qids: Patch Report scorecard only — up to 10 comma-separated
                QIDs for vulnerabilities with available patches.
            missing_qids: Patch Report scorecard only — 1-2 comma-separated
                QIDs for missing-software information-gathered checks.
                patch_qids or missing_qids is required for a Patch Report
                scorecard.

        Returns:
            SIMPLE_RETURN with the new report ID, or an error dict.
        """
        data = {
            "action": "launch",
            "name": name,
            "output_format": output_format,
            "report_title": report_title,
            "hide_header": hide_header,
            "pdf_password": pdf_password,
            "recipient_group": recipient_group,
            "recipient_group_id": recipient_group_id,
            "source": source,
            "asset_groups": asset_groups,
            "all_asset_groups": all_asset_groups,
            "business_unit": business_unit,
            "division": division,
            "function": function,
            "location": location,
            "patch_qids": patch_qids,
            "missing_qids": missing_qids,
        }
        return self._fo("/api/2.0/fo/report/scorecard/", method="POST", data=data)

    def cancel_report(self, id: int) -> dict[str, Any]:
        """Cancel a running report.

        Args:
            id: Report ID of a report currently in the "Running" state.

        Returns:
            SIMPLE_RETURN status, or an error dict.
        """
        data = {"action": "cancel", "id": id}
        return self._fo("/api/2.0/fo/report/", method="POST", data=data)

    def launch_scheduled_report(self, id: int) -> dict[str, Any]:
        """Launch a scheduled report immediately.

        Args:
            id: A valid scheduled report ID (see ``scheduled_reports_list``).

        Returns:
            SIMPLE_RETURN status, or an error dict.
        """
        data = {"action": "launch_now", "id": id}
        return self._fo("/api/2.0/fo/schedule/report/", method="POST", data=data)

    def asset_search_report(
        self,
        output_format: str = "xml",
        tracking_method: str | None = None,
        ips: str | None = None,
        ips_network_id: str | None = None,
        asset_group_ids: str | None = None,
        asset_groups: str | None = None,
        assets_in_my_network_only: bool | None = None,
        ec2_instance_status: str | None = None,
        ec2_instance_id: str | None = None,
        ec2_instance_id_modifier: str | None = None,
        azure_vm_state: str | None = None,
        azure_vm_id: str | None = None,
        azure_vm_id_modifier: str | None = None,
        gcp_vm_instance_state: str | None = None,
        gcp_vm_instance_id: str | None = None,
        gcp_vm_instance_id_modifier: str | None = None,
        display_ag_titles: bool | None = None,
        ports: str | None = None,
        services: str | None = None,
        qids: str | None = None,
        qid_with_text: str | None = None,
        qid_with_modifier: str | None = None,
        use_tags: bool | None = None,
        tag_set_by: str | None = None,
        tag_include_selector: str | None = None,
        tag_exclude_selector: str | None = None,
        tag_set_include: str | None = None,
        tag_set_exclude: str | None = None,
        first_found_days: int | None = None,
        first_found_modifier: str | None = None,
        last_vm_scan_days: int | None = None,
        last_vm_scan_modifier: str | None = None,
        last_pc_scan_days: int | None = None,
        last_pc_scan_modifier: str | None = None,
        last_scap_scan_days: int | None = None,
        last_scap_scan_modifier: str | None = None,
        dns_name: str | None = None,
        dns_modifier: str | None = None,
        netbios_name: str | None = None,
        netbios_modifier: str | None = None,
        os_cpe_name: str | None = None,
        os_cpe_modifier: str | None = None,
        os_name: str | None = None,
        os_modifier: str | None = None,
    ) -> dict[str, Any]:
        """Run an immediate (non-queued) asset search report.

        One of ips, asset_groups, asset_group_ids, or use_tags (+
        tag_set_include) must be given to select the target hosts.

        Args:
            output_format: "csv" or "xml" (default "xml").
            tracking_method: Restrict to hosts with this tracking method —
                "IP", "DNS", "NETBIOS", "AZURE VM", "EC2", "GCP Compute
                Engine", or "AGENT".
            ips: Comma-separated IPs/ranges (e.g. "10.10.10.1-10.10.10.100").
            ips_network_id: Network ID applied to `ips`. Default "ALL".
            asset_group_ids: Comma-separated asset group IDs to include.
            asset_groups: Comma-separated asset group titles to include.
            assets_in_my_network_only: Set True to restrict to the specified
                asset groups and/or IP ranges only (valid for the 'All' asset
                group and/or specified IP ranges).
            ec2_instance_status: EC2 instance status filter — one of RUNNING,
                TERMINATED, PENDING, STOPPING, SHUTTING_DOWN, STOPPED
                (case-sensitive). Valid only with tracking_method=EC2 or AGENT.
            ec2_instance_id: EC2 instance ID to search for. Requires
                ec2_instance_id_modifier.
            ec2_instance_id_modifier: How to match ec2_instance_id —
                "beginning with", "containing", "matching", "ending with", or
                "not empty".
            azure_vm_state: Azure VM state filter — STARTING, RUNNING,
                STOPPING, STOPPED, DEALLOCATING, DEALLOCATED, or UNKNOWN
                (case-sensitive). Valid only with tracking_method=AZURE VM or
                AGENT.
            azure_vm_id: Azure VM ID to search for. Requires
                azure_vm_id_modifier.
            azure_vm_id_modifier: How to match azure_vm_id — "beginning with",
                "containing", "matching", "ending with", or "not empty".
            gcp_vm_instance_state: GCP VM state filter — PROVISIONING,
                STAGING, RUNNING, STOPPING, STOPPED, REPAIRING, TERMINATED,
                SUSPENDING, or SUSPENDED (case-sensitive). Valid only with
                tracking_method=GCP or AGENT.
            gcp_vm_instance_id: GCP VM instance ID to search for. Requires
                gcp_vm_instance_id_modifier.
            gcp_vm_instance_id_modifier: How to match gcp_vm_instance_id —
                "beginning with", "containing", "matching", "ending with", or
                "not empty".
            display_ag_titles: Set True to display asset group titles for
                each host in the output.
            ports: Comma-separated open ports to filter on (max 10 values).
            services: Comma-separated running services to filter on (max 10
                values).
            qids: Comma-separated KnowledgeBase QIDs to filter on (max 20).
            qid_with_text: Text to match within QID titles. Requires qids.
            qid_with_modifier: How to match qid_with_text — "beginning with",
                "containing", "matching", or "ending with".
            use_tags: Set True to select hosts by asset tag instead of
                ips/asset groups.
            tag_set_by: "id" (default) or "name" — how tag_set_include/
                tag_set_exclude are given.
            tag_include_selector: "any" (default) or "all" — how
                tag_set_include tags combine.
            tag_exclude_selector: "any" (default) or "all" — how
                tag_set_exclude tags combine.
            tag_set_include: Comma-separated tag IDs/names to include
                (use_tags=True only).
            tag_set_exclude: Comma-separated tag IDs/names to exclude
                (use_tags=True only).
            first_found_days: Number of days for the first-found date range.
                Requires first_found_modifier.
            first_found_modifier: "within" or "not within" — how
                first_found_days is applied.
            last_vm_scan_days: Number of days for the last VM scan date
                range. Requires last_vm_scan_modifier.
            last_vm_scan_modifier: "within" or "not within" — how
                last_vm_scan_days is applied.
            last_pc_scan_days: Number of days for the last Policy Compliance
                scan date range (requires the PC module). Requires
                last_pc_scan_modifier.
            last_pc_scan_modifier: "within" or "not within" — how
                last_pc_scan_days is applied.
            last_scap_scan_days: Number of days for the last SCAP scan date
                range (requires the PC module). Requires
                last_scap_scan_modifier.
            last_scap_scan_modifier: "within" or "not within" — how
                last_scap_scan_days is applied.
            dns_name: DNS name to search for. Requires dns_modifier.
            dns_modifier: How to match dns_name — "beginning with",
                "containing", "matching", "ending with", or "not empty".
            netbios_name: NetBIOS name to search for. Requires
                netbios_modifier.
            netbios_modifier: How to match netbios_name — "beginning with",
                "containing", "matching", "ending with", or "not empty".
            os_cpe_name: OS CPE name to search for. Requires os_cpe_modifier.
            os_cpe_modifier: How to match os_cpe_name — "beginning with",
                "containing", "matching", "ending with", or "not empty".
            os_name: Operating system name to search for. Requires
                os_modifier.
            os_modifier: How to match os_name — "beginning with",
                "containing", "matching", or "ending with".

        Returns:
            Parsed ASSET_SEARCH_REPORT dict when output_format="xml";
            otherwise ``{"raw": <CSV text>}``.
        """
        params = {
            "action": "search",
            "output_format": output_format,
            "tracking_method": tracking_method,
            "ips": ips,
            "ips_network_id": ips_network_id,
            "asset_group_ids": asset_group_ids,
            "asset_groups": asset_groups,
            "assets_in_my_network_only": assets_in_my_network_only,
            "ec2_instance_status": ec2_instance_status,
            "ec2_instance_id": ec2_instance_id,
            "ec2_instance_id_modifier": ec2_instance_id_modifier,
            "azure_vm_state": azure_vm_state,
            "azure_vm_id": azure_vm_id,
            "azure_vm_id_modifier": azure_vm_id_modifier,
            "gcp_vm_instance_state": gcp_vm_instance_state,
            "gcp_vm_instance_id": gcp_vm_instance_id,
            "gcp_vm_instance_id_modifier": gcp_vm_instance_id_modifier,
            "display_ag_titles": display_ag_titles,
            "ports": ports,
            "services": services,
            "qids": qids,
            "qid_with_text": qid_with_text,
            "qid_with_modifier": qid_with_modifier,
            "use_tags": use_tags,
            "tag_set_by": tag_set_by,
            "tag_include_selector": tag_include_selector,
            "tag_exclude_selector": tag_exclude_selector,
            "tag_set_include": tag_set_include,
            "tag_set_exclude": tag_set_exclude,
            "first_found_days": first_found_days,
            "first_found_modifier": first_found_modifier,
            "last_vm_scan_days": last_vm_scan_days,
            "last_vm_scan_modifier": last_vm_scan_modifier,
            "last_pc_scan_days": last_pc_scan_days,
            "last_pc_scan_modifier": last_pc_scan_modifier,
            "last_scap_scan_days": last_scap_scan_days,
            "last_scap_scan_modifier": last_scap_scan_modifier,
            "dns_name": dns_name,
            "dns_modifier": dns_modifier,
            "netbios_name": netbios_name,
            "netbios_modifier": netbios_modifier,
            "os_cpe_name": os_cpe_name,
            "os_cpe_modifier": os_cpe_modifier,
            "os_name": os_name,
            "os_modifier": os_modifier,
        }
        parse = output_format == "xml"
        return self._fo("/api/2.0/fo/report/asset/", method="GET", params=params, parse=parse)

    # --------------------------- destructive --------------------------- #
    def delete_report(self, id: int, confirm: str | None = None) -> dict[str, Any]:
        """Permanently delete a saved report from Report Share. IRREVERSIBLE.

        Gated: requires the console to be started with
        QUALYS_ENABLE_DESTRUCTIVE and the caller to pass confirm=<id>.

        Args:
            id: Report ID of a saved report in the "Finished" state.
            confirm: Must equal ``str(id)`` to proceed.

        Returns:
            SIMPLE_RETURN status, or a confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=str(id))
        if guard:
            return guard
        data = {"action": "delete", "id": id}
        return self._fo("/api/2.0/fo/report/", method="POST", data=data)
