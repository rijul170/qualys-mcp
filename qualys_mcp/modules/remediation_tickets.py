"""VM Remediation Tickets module (classic FO API) — read/write/destructive.

Covers listing, editing, and deleting remediation tickets created by the VM
Remediation Workflow, plus the related "ignore vulnerability on host" action
(which itself opens/closes Closed/Ignored tickets).

Endpoints (all served from the classic FO host; ``ticket_*``/``get_tickets``
live under ``/msp/`` rather than ``/api/2.0/fo/``, matching the API guide):
* ``/msp/ticket_list.php`` (view ticket list)
* ``/msp/get_tickets.php`` (get ticket information)
* ``/msp/ticket_edit.php`` (bulk edit tickets)
* ``/msp/ticket_delete.php`` (bulk delete tickets)
* ``/msp/ticket_list_deleted.php`` (view deleted ticket list)
* ``/api/2.0/fo/ignore_vuln/index.php`` (ignore/restore vulnerabilities on hosts)

Docs: Qualys VM/PC API User Guide — "VM Remediation Tickets".
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class RemediationTicketsModule(BaseModule):
    """View, edit, and delete VM remediation tickets; ignore vulns on hosts."""

    module_label = "remediation_tickets"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(server, self.view_ticket_list, "view_ticket_list", tier="read")
        self._add_tool(server, self.get_ticket_info, "get_ticket_info", tier="read")
        self._add_tool(
            server, self.view_deleted_tickets, "view_deleted_tickets", tier="read"
        )
        # Writes
        self._add_tool(server, self.edit_tickets, "edit_tickets", tier="write")
        self._add_tool(server, self.set_ignore_vulns, "set_ignore_vulns", tier="write")
        # Destructive
        self._add_tool(server, self.delete_tickets, "delete_tickets", tier="destructive")

    # ------------------------------ reads ------------------------------ #
    def view_ticket_list(
        self,
        ticket_numbers: str | None = None,
        since_ticket_number: int | None = None,
        until_ticket_number: int | None = None,
        show_vuln_details: bool | None = None,
        ticket_assignee: str | None = None,
        overdue: bool | None = None,
        invalid: bool | None = None,
        states: str | None = None,
        modified_since_datetime: str | None = None,
        unmodified_since_datetime: str | None = None,
        ips: str | None = None,
        asset_groups: str | None = None,
        dns_contains: str | None = None,
        netbios_contains: str | None = None,
        host_id: int | None = None,
        show_host_id: bool | None = None,
        vuln_severities: str | None = None,
        potential_vuln_severities: str | None = None,
        qids: str | None = None,
        vuln_title_contains: str | None = None,
        vuln_details_contains: str | None = None,
        vendor_ref_contains: str | None = None,
    ) -> dict[str, Any]:
        """View remediation tickets in the account. At least one filter is required.

        A maximum of 1,000 tickets are returned per call; a "Truncated after
        1,000 records" message with the last ticket number is appended when
        more match. Page through results with since_ticket_number.

        Args:
            ticket_numbers: Ticket numbers and/or ranges, e.g. "1800,2000-2100".
            since_ticket_number: Only tickets with number >= this value.
            until_ticket_number: Only tickets with number <= this value.
            show_vuln_details: Include vulnerability threat/impact/solution/
                results details in the output (default False).
            ticket_assignee: User login of the ticket assignee.
            overdue: True for overdue tickets only, False for non-overdue only.
                Both are selected by default.
            invalid: True for invalid tickets only, False for valid only. Both
                are selected by default.
            states: Comma-separated ticket states — "OPEN" (Open/Reopened),
                "RESOLVED", "CLOSED" (Closed/Fixed), or "IGNORED"
                (Closed/Ignored). Use states="IGNORED" to list ignored
                vulnerabilities on hosts.
            modified_since_datetime: ISO datetime (YYYY-MM-DD[THH:MM:SSZ]) —
                only tickets modified on/after this date/time.
            unmodified_since_datetime: ISO datetime (YYYY-MM-DD[THH:MM:SSZ])
                — only tickets NOT modified on/after this date/time.
            ips: Comma-separated IPs/ranges of hosts with tickets.
            asset_groups: Comma-separated asset group titles; "All" selects
                every IP in the account.
            dns_contains: Substring to match against host DNS name (max 100
                chars).
            netbios_contains: Substring to match against host NetBIOS name
                (max 100 chars).
            host_id: A single asset's HOST_ID.
            show_host_id: Include HOST_ID in the output (default False).
            vuln_severities: Comma-separated severity levels (1-5) for
                confirmed vulnerabilities.
            potential_vuln_severities: Comma-separated severity levels (1-5)
                for potential vulnerabilities.
            qids: Comma-separated QIDs (max 10).
            vuln_title_contains: Substring to match against the KnowledgeBase
                vulnerability title (max 100 chars).
            vuln_details_contains: Substring to match against vulnerability
                threat/impact/solution/results text (max 100 chars).
            vendor_ref_contains: Substring to match against the vendor
                reference (max 100 chars).

        Returns:
            Parsed ticket list output.
        """
        params = {
            "ticket_numbers": ticket_numbers,
            "since_ticket_number": since_ticket_number,
            "until_ticket_number": until_ticket_number,
            "show_vuln_details": show_vuln_details,
            "ticket_assignee": ticket_assignee,
            "overdue": overdue,
            "invalid": invalid,
            "states": states,
            "modified_since_datetime": modified_since_datetime,
            "unmodified_since_datetime": unmodified_since_datetime,
            "ips": ips,
            "asset_groups": asset_groups,
            "dns_contains": dns_contains,
            "netbios_contains": netbios_contains,
            "host_id": host_id,
            "show_host_id": show_host_id,
            "vuln_severities": vuln_severities,
            "potential_vuln_severities": potential_vuln_severities,
            "qids": qids,
            "vuln_title_contains": vuln_title_contains,
            "vuln_details_contains": vuln_details_contains,
            "vendor_ref_contains": vendor_ref_contains,
        }
        return self._fo("/msp/ticket_list.php", method="GET", params=params)

    def get_ticket_info(
        self,
        ticket_numbers: str | None = None,
        since: str | None = None,
        state: str | None = None,
        vuln_details: bool | None = None,
    ) -> dict[str, Any]:
        """Get remediation ticket information for third-party integration.

        Either ticket_numbers or since must be specified.

        Args:
            ticket_numbers: Comma-separated ticket numbers (max 1,000).
            since: ISO datetime (YYYY-MM-DDTHH:MM:SSZ) — start of the update
                window; the window ends at call time.
            state: Restrict to tickets in this state — "OPEN", "RESOLVED", or
                "CLOSED". All states are returned when omitted.
            vuln_details: Include vulnerability threat/impact/solution/
                results details (default False).

        Returns:
            Parsed remediation ticket information report.
        """
        params = {
            "ticket_numbers": ticket_numbers,
            "since": since,
            "state": state,
            "vuln_details": vuln_details,
        }
        return self._fo("/msp/get_tickets.php", method="GET", params=params)

    def view_deleted_tickets(
        self,
        ticket_numbers: str | None = None,
        since_ticket_number: int | None = None,
        until_ticket_number: int | None = None,
        deleted_since_datetime: str | None = None,
        deleted_before_datetime: str | None = None,
    ) -> dict[str, Any]:
        """List deleted remediation tickets. At least one filter is required.

        Manager user role is required. A maximum of 1,000 deleted tickets are
        returned per call; a truncation message with the last ticket number
        is appended when more match.

        Args:
            ticket_numbers: Ticket numbers and/or ranges, e.g. "120-200".
            since_ticket_number: Only tickets with number >= this value.
            until_ticket_number: Only tickets with number <= this value.
            deleted_since_datetime: ISO datetime (YYYY-MM-DD[THH:MM:SSZ]) —
                only tickets deleted on/after this date/time.
            deleted_before_datetime: ISO datetime (YYYY-MM-DD[THH:MM:SSZ]) —
                only tickets deleted on/before this date/time.

        Returns:
            Parsed deleted ticket list output.
        """
        params = {
            "ticket_numbers": ticket_numbers,
            "since_ticket_number": since_ticket_number,
            "until_ticket_number": until_ticket_number,
            "deleted_since_datetime": deleted_since_datetime,
            "deleted_before_datetime": deleted_before_datetime,
        }
        return self._fo("/msp/ticket_list_deleted.php", method="GET", params=params)

    # ------------------------------ writes ----------------------------- #
    def edit_tickets(
        self,
        ticket_numbers: str | None = None,
        since_ticket_number: int | None = None,
        until_ticket_number: int | None = None,
        ticket_assignee: str | None = None,
        overdue: bool | None = None,
        invalid: bool | None = None,
        states: str | None = None,
        modified_since_datetime: str | None = None,
        unmodified_since_datetime: str | None = None,
        ips: str | None = None,
        asset_groups: str | None = None,
        dns_contains: str | None = None,
        netbios_contains: str | None = None,
        host_id: int | None = None,
        vuln_severities: str | None = None,
        potential_vuln_severities: str | None = None,
        qids: str | None = None,
        vuln_title_contains: str | None = None,
        vuln_details_contains: str | None = None,
        vendor_ref_contains: str | None = None,
        change_assignee: str | None = None,
        change_state: str | None = None,
        add_comment: str | None = None,
        reopen_ignored_days: int | None = None,
    ) -> dict[str, Any]:
        """Bulk-edit remediation tickets matching the given selection filters.

        At least one selection filter and at least one edit parameter
        (change_assignee, change_state, add_comment, reopen_ignored_days) is
        required. A maximum of 20,000 tickets can be edited per call.

        Args:
            ticket_numbers: Ticket numbers and/or ranges, e.g. "1800,2000-2100".
            since_ticket_number: Only tickets with number >= this value.
            until_ticket_number: Only tickets with number <= this value.
            ticket_assignee: User login of the current ticket assignee
                (selection filter).
            overdue: True for overdue tickets only, False for non-overdue only.
            invalid: True for invalid tickets only, False for valid only.
            states: Comma-separated ticket states to select — OPEN, RESOLVED,
                CLOSED, IGNORED.
            modified_since_datetime: ISO datetime (YYYY-MM-DD[THH:MM:SSZ]) —
                only tickets modified on/after this date/time.
            unmodified_since_datetime: ISO datetime (YYYY-MM-DD[THH:MM:SSZ])
                — only tickets NOT modified on/after this date/time.
            ips: Comma-separated IPs/ranges of hosts with tickets to select.
            asset_groups: Comma-separated asset group titles to select
                ("All" = every IP).
            dns_contains: Substring to match against host DNS name (max 100
                chars).
            netbios_contains: Substring to match against host NetBIOS name
                (max 100 chars).
            host_id: A single asset's HOST_ID.
            vuln_severities: Comma-separated severity levels (1-5) for
                confirmed vulnerabilities.
            potential_vuln_severities: Comma-separated severity levels (1-5)
                for potential vulnerabilities.
            qids: Comma-separated QIDs (max 10).
            vuln_title_contains: Substring to match against the KnowledgeBase
                vulnerability title (max 100 chars).
            vuln_details_contains: Substring to match against vulnerability
                threat/impact/solution/results text (max 100 chars).
            vendor_ref_contains: Substring to match against the vendor
                reference (max 100 chars).
            change_assignee: New assignee user login for all selected
                tickets. The account must not have the Contact role and must
                own the ticketed hosts.
            change_state: New state for all selected tickets — "OPEN"
                (Open/Reopened), "RESOLVED", or "IGNORED" (Closed/Ignored).
                Not all transitions are valid (e.g. Closed/Ignored ->
                Resolved is invalid); see "Ticket State/Status Transitions"
                in the API guide.
            add_comment: Comment text to add to all selected tickets (max
                2,000 chars).
            reopen_ignored_days: Reopen Closed/Ignored tickets after N days
                (1-730) if the issue still exists.

        Returns:
            Parsed ticket edit output (counts of tickets updated), or an
            error dict.
        """
        if change_state is not None and change_state.upper() not in (
            "OPEN",
            "RESOLVED",
            "IGNORED",
        ):
            return {"error": "change_state must be one of: OPEN, RESOLVED, IGNORED"}
        data = {
            "ticket_numbers": ticket_numbers,
            "since_ticket_number": since_ticket_number,
            "until_ticket_number": until_ticket_number,
            "ticket_assignee": ticket_assignee,
            "overdue": overdue,
            "invalid": invalid,
            "states": states,
            "modified_since_datetime": modified_since_datetime,
            "unmodified_since_datetime": unmodified_since_datetime,
            "ips": ips,
            "asset_groups": asset_groups,
            "dns_contains": dns_contains,
            "netbios_contains": netbios_contains,
            "host_id": host_id,
            "vuln_severities": vuln_severities,
            "potential_vuln_severities": potential_vuln_severities,
            "qids": qids,
            "vuln_title_contains": vuln_title_contains,
            "vuln_details_contains": vuln_details_contains,
            "vendor_ref_contains": vendor_ref_contains,
            "change_assignee": change_assignee,
            "change_state": change_state,
            "add_comment": add_comment,
            "reopen_ignored_days": reopen_ignored_days,
        }
        return self._fo("/msp/ticket_edit.php", method="POST", data=data)

    def set_ignore_vulns(
        self,
        qids: str,
        comments: str,
        action: str = "ignore",
        reopen_ignored_days: int | None = None,
        reopen_ignored_date: str | None = None,
        asset_groups: str | None = None,
        ips: str | None = None,
        network_id: str | None = None,
        tag_set_include: str | None = None,
        tag_set_exclude: str | None = None,
        tag_set_by: str | None = None,
        tag_include_selector: str | None = None,
        tag_exclude_selector: str | None = None,
        use_ip_nt_range_tags_include: bool | None = None,
        use_ip_nt_range_tags_exclude: bool | None = None,
        dns_contains: str | None = None,
        netbios_contains: str | None = None,
    ) -> dict[str, Any]:
        """Ignore or restore vulnerabilities on hosts (vulnerability/host pairs).

        Ignored issues are excluded from scan/host-information/asset-search
        reports and other UI views. Ignoring a vulnerability closes (or
        creates and closes) its remediation ticket as Closed/Ignored;
        restoring reopens the ticket as Open/Reopened. Exactly one host
        selection parameter should be given (asset_groups, ips, network_id,
        tag_set_include/tag_set_exclude, dns_contains, or netbios_contains).
        QIDs 38175, 82043, 38228, and 82051 cannot be ignored; Information
        Gathered issues cannot be ignored.

        Args:
            qids: Comma-separated QIDs to ignore/restore (max 10).
            comments: Comment stored with the ignored vulnerabilities and
                shown in the Qualys UI (max 255 chars).
            action: "ignore" (default) or "restore" (un-ignore). Must be
                specified explicitly when restoring.
            reopen_ignored_days: Ignore action only — auto-reopen the
                ignored vulnerability if detected again after N days (1-730).
            reopen_ignored_date: Ignore action only — auto-reopen the
                ignored vulnerability if detected again after this date
                (YYYY-MM-DD).
            asset_groups: Comma-separated asset group titles (max 5); "All"
                is valid.
            ips: Comma-separated IPs/ranges (max 512 chars).
            network_id: Network Support feature only — network ID for the
                record. Defaults to the Global Default Network when omitted.
            tag_set_include: Comma-separated tag IDs/names identifying hosts
                to include.
            tag_set_exclude: Comma-separated tag IDs/names identifying hosts
                to exclude.
            tag_set_by: "id" (default) or "name" — how tag_set_include/
                tag_set_exclude are given.
            tag_include_selector: "any" (default) or "all" — how
                tag_set_include tags combine.
            tag_exclude_selector: "any" (default) or "all" — how
                tag_set_exclude tags combine.
            use_ip_nt_range_tags_include: Set True to only match tags with
                the dynamic "IP address in Network Range(s)" rule when
                including by tag.
            use_ip_nt_range_tags_exclude: Set True to only match tags with
                the dynamic "IP address in Network Range(s)" rule when
                excluding by tag.
            dns_contains: Substring to match against host DNS name (max 100
                chars).
            netbios_contains: Substring to match against host NetBIOS name
                (max 100 chars).

        Returns:
            Parsed ignore_vuln output, or an error dict.
        """
        data = {
            "action": action,
            "qids": qids,
            "comments": comments,
            "reopen_ignored_days": reopen_ignored_days,
            "reopen_ignored_date": reopen_ignored_date,
            "asset_groups": asset_groups,
            "ips": ips,
            "network_id": network_id,
            "tag_set_include": tag_set_include,
            "tag_set_exclude": tag_set_exclude,
            "tag_set_by": tag_set_by,
            "tag_include_selector": tag_include_selector,
            "tag_exclude_selector": tag_exclude_selector,
            "use_ip_nt_range_tags_include": use_ip_nt_range_tags_include,
            "use_ip_nt_range_tags_exclude": use_ip_nt_range_tags_exclude,
            "dns_contains": dns_contains,
            "netbios_contains": netbios_contains,
        }
        # TODO(verify): the API guide only shows this endpoint invoked via
        # GET-style sample URLs; using POST here since the call mutates
        # ticket/host state (per the guide's write-action convention). Confirm
        # against a live console whether GET is also accepted/required.
        return self._fo("/api/2.0/fo/ignore_vuln/index.php", method="POST", data=data)

    # --------------------------- destructive --------------------------- #
    def delete_tickets(
        self,
        ticket_numbers: str | None = None,
        since_ticket_number: int | None = None,
        until_ticket_number: int | None = None,
        ticket_assignee: str | None = None,
        overdue: bool | None = None,
        invalid: bool | None = None,
        states: str | None = None,
        modified_since_datetime: str | None = None,
        unmodified_since_datetime: str | None = None,
        ips: str | None = None,
        asset_groups: str | None = None,
        dns_contains: str | None = None,
        netbios_contains: str | None = None,
        host_id: int | None = None,
        vuln_severities: str | None = None,
        potential_vuln_severities: str | None = None,
        qids: str | None = None,
        vuln_title_contains: str | None = None,
        vuln_details_contains: str | None = None,
        vendor_ref_contains: str | None = None,
        confirm: str | None = None,
    ) -> dict[str, Any]:
        """Permanently delete remediation tickets matching the given filters.

        IRREVERSIBLE. At least one selection filter is required. A maximum of
        20,000 tickets can be deleted per call.

        Gated: requires the console to be started with
        QUALYS_ENABLE_DESTRUCTIVE and the caller to pass a matching confirm
        value (see below).

        Args:
            ticket_numbers: Ticket numbers and/or ranges, e.g. "1800,2000-2100".
            since_ticket_number: Only tickets with number >= this value.
            until_ticket_number: Only tickets with number <= this value.
            ticket_assignee: User login of the ticket assignee.
            overdue: True for overdue tickets only, False for non-overdue only.
            invalid: True for invalid tickets only, False for valid only.
            states: Comma-separated ticket states — OPEN, RESOLVED, CLOSED,
                IGNORED.
            modified_since_datetime: ISO datetime (YYYY-MM-DD[THH:MM:SSZ]) —
                only tickets modified on/after this date/time.
            unmodified_since_datetime: ISO datetime (YYYY-MM-DD[THH:MM:SSZ])
                — only tickets NOT modified on/after this date/time.
            ips: Comma-separated IPs/ranges of hosts with tickets.
            asset_groups: Comma-separated asset group titles ("All" = every
                IP).
            dns_contains: Substring to match against host DNS name (max 100
                chars).
            netbios_contains: Substring to match against host NetBIOS name
                (max 100 chars).
            host_id: A single asset's HOST_ID.
            vuln_severities: Comma-separated severity levels (1-5) for
                confirmed vulnerabilities.
            potential_vuln_severities: Comma-separated severity levels (1-5)
                for potential vulnerabilities.
            qids: Comma-separated QIDs (max 10).
            vuln_title_contains: Substring to match against the KnowledgeBase
                vulnerability title (max 100 chars).
            vuln_details_contains: Substring to match against vulnerability
                threat/impact/solution/results text (max 100 chars).
            vendor_ref_contains: Substring to match against the vendor
                reference (max 100 chars).
            confirm: This API deletes tickets in bulk by filter rather than
                by a single ID. Must equal ``ticket_numbers`` when it is
                specified; otherwise must equal the literal string
                ``"ALL_MATCHING_FILTERS"`` to proceed.

        Returns:
            Parsed ticket delete output (count of tickets deleted), or a
            confirmation/error dict.
        """
        expected = ticket_numbers if ticket_numbers else "ALL_MATCHING_FILTERS"
        guard = self._confirm_or_error(confirm, expected=expected)
        if guard:
            return guard
        data = {
            "ticket_numbers": ticket_numbers,
            "since_ticket_number": since_ticket_number,
            "until_ticket_number": until_ticket_number,
            "ticket_assignee": ticket_assignee,
            "overdue": overdue,
            "invalid": invalid,
            "states": states,
            "modified_since_datetime": modified_since_datetime,
            "unmodified_since_datetime": unmodified_since_datetime,
            "ips": ips,
            "asset_groups": asset_groups,
            "dns_contains": dns_contains,
            "netbios_contains": netbios_contains,
            "host_id": host_id,
            "vuln_severities": vuln_severities,
            "potential_vuln_severities": potential_vuln_severities,
            "qids": qids,
            "vuln_title_contains": vuln_title_contains,
            "vuln_details_contains": vuln_details_contains,
            "vendor_ref_contains": vendor_ref_contains,
        }
        return self._fo("/msp/ticket_delete.php", method="POST", data=data)
