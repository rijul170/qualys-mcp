"""Excluded Hosts module (classic FO API) — hosts exempt from scanning.

Covers:
* Excluded Host List (``/api/2.0/fo/asset/excluded_ip/`` action=list).
* Excluded Hosts Change History (``/api/2.0/fo/asset/excluded_ip/history/`` action=list).
* Manage Excluded Hosts — add (action=add), remove (action=remove), and
  remove-all (action=remove_all, DESTRUCTIVE — wipes the entire excluded list).

Docs: Qualys VM/PC API User Guide — "Assets" chapter ("Excluded Host List",
"Excluded Hosts Change History", "Manage Excluded Hosts").
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class ExcludedHostsModule(BaseModule):
    """List, audit, and manage the subscription's excluded-host list."""

    module_label = "excluded_hosts"

    def register_tools(self, server: FastMCP) -> None:
        self._add_tool(server, self.list_excluded_hosts, "list_excluded_hosts", tier="read")
        self._add_tool(
            server,
            self.list_excluded_hosts_history,
            "list_excluded_hosts_history",
            tier="read",
        )
        self._add_tool(server, self.add_excluded_hosts, "add_excluded_hosts", tier="write")
        self._add_tool(
            server, self.remove_excluded_hosts, "remove_excluded_hosts", tier="write"
        )
        self._add_tool(
            server,
            self.remove_all_excluded_hosts,
            "remove_all_excluded_hosts",
            tier="destructive",
        )

    # ------------------------------------------------------------------ #
    # Reads
    # ------------------------------------------------------------------ #
    def list_excluded_hosts(
        self,
        ips: str | None = None,
        network_id: str | None = None,
        ag_ids: str | None = None,
        ag_titles: str | None = None,
        use_tags: bool | None = None,
        tag_set_by: str | None = None,
        tag_include_selector: str | None = None,
        tag_exclude_selector: str | None = None,
        tag_set_include: str | None = None,
        tag_set_exclude: str | None = None,
        echo_request: bool | None = None,
    ) -> dict[str, Any]:
        """List hosts on the excluded-hosts list (hosts that will not be scanned).

        Args:
            ips: Comma-separated excluded IPs/ranges to restrict the list to. When
                omitted, all excluded IPs/ranges in the account are listed.
            network_id: Restrict to a custom network ID, or comma-separated network
                names/IDs (Network Support feature only).
            ag_ids: Comma-separated asset group IDs. Mutually exclusive with ag_titles.
            ag_titles: Comma-separated asset group titles. Mutually exclusive with ag_ids.
            use_tags: True to select excluded hosts by asset tags.
            tag_set_by: "id" (default) or "name" — how tag_set_include/exclude identify tags.
            tag_include_selector: "any" (default) or "all".
            tag_exclude_selector: "any" (default) or "all".
            tag_set_include: Comma-separated tag IDs/names to include (requires use_tags=True).
            tag_set_exclude: Comma-separated tag IDs/names to exclude (requires use_tags=True).
            echo_request: Echo input parameters back in the output.

        Returns:
            Parsed IP_LIST_OUTPUT (an <IP_SET> of excluded <IP>/<IP_RANGE> entries,
            each annotated with network_id and optional expiration_date).
        """
        params = {
            "action": "list",
            "ips": ips,
            "network_id": network_id,
            "ag_ids": ag_ids,
            "ag_titles": ag_titles,
            "use_tags": use_tags,
            "tag_set_by": tag_set_by,
            "tag_include_selector": tag_include_selector,
            "tag_exclude_selector": tag_exclude_selector,
            "tag_set_include": tag_set_include,
            "tag_set_exclude": tag_set_exclude,
            "echo_request": echo_request,
        }
        return self._fo("/api/2.0/fo/asset/excluded_ip/", method="GET", params=params)

    def list_excluded_hosts_history(
        self,
        ips: str | None = None,
        network_id: str | None = None,
        ids: str | None = None,
        id_min: int | None = None,
        id_max: int | None = None,
        echo_request: bool | None = None,
    ) -> dict[str, Any]:
        """View the change history (add/remove events) for excluded hosts.

        Returns change history for all relevant IPs in the subscription
        regardless of whether the caller currently has access to those IPs.
        History record IDs are listed in decreasing order.

        Args:
            ips: Comma-separated excluded IPs/ranges to restrict the history to.
            network_id: Restrict to a custom network ID (Network Support feature only).
            ids: Comma-separated history record IDs to match exactly.
            id_min: Minimum history record ID (inclusive).
            id_max: Maximum history record ID (inclusive).
            echo_request: Echo input parameters back in the output.

        Returns:
            Parsed HISTORY_LIST_OUTPUT (each <HISTORY> entry has an IP_SET,
            ACTION, DATETIME, USER_LOGIN, and COMMENTS).
        """
        params = {
            "action": "list",
            "ips": ips,
            "network_id": network_id,
            "ids": ids,
            "id_min": id_min,
            "id_max": id_max,
            "echo_request": echo_request,
        }
        return self._fo("/api/2.0/fo/asset/excluded_ip/history/", method="GET", params=params)

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #
    def add_excluded_hosts(
        self,
        ips: str,
        comment: str,
        expiry_days: int | None = None,
        dg_names: str | None = None,
        network_id: str | None = None,
    ) -> dict[str, Any]:
        """Add hosts (IPs) to the excluded-hosts list. Excluded hosts are not scanned.

        Args:
            ips: Comma-separated IPv4 singletons/ranges to exclude (e.g.
                "10.10.10.13,10.10.10.25-10.10.10.29").
            comment: User-defined notes (up to 1024 characters).
            expiry_days: Number of days the exclusion is valid. When the
                expiration is reached the IPs are automatically removed from the
                list and become scannable again. Omit for no expiration.
            dg_names: Comma-separated distribution group names to notify 7 days
                before the hosts are removed from the list (max 15 groups).
            network_id: Network ID to assign the excluded IPs to (only valid when
                the caller has access to more than one network; defaults to the
                caller's default network).

        Returns:
            SIMPLE_RETURN confirming the IPs were added (or already present), or
            an error dict.
        """
        data = {
            "action": "add",
            "ips": ips,
            "comment": comment,
            "expiry_days": expiry_days,
            "dg_names": dg_names,
            "network_id": network_id,
        }
        return self._fo("/api/2.0/fo/asset/excluded_ip/", method="POST", data=data)

    def remove_excluded_hosts(
        self, ips: str, comment: str, network_id: str | None = None
    ) -> dict[str, Any]:
        """Remove specific hosts from the excluded-hosts list (they become scannable again).

        Args:
            ips: Comma-separated IPv4 singletons/ranges to remove from the
                excluded list (e.g. "10.10.34.250-10.10.34.254").
            comment: User-defined notes (up to 1024 characters).
            network_id: Network ID the excluded IPs are assigned to (only valid
                when the caller has access to more than one network; defaults to
                the caller's default network).

        Returns:
            SIMPLE_RETURN confirming the IPs were removed, or an error dict.
        """
        data = {
            "action": "remove",
            "ips": ips,
            "comment": comment,
            "network_id": network_id,
        }
        return self._fo("/api/2.0/fo/asset/excluded_ip/", method="POST", data=data)

    # ------------------------------------------------------------------ #
    # Destructive
    # ------------------------------------------------------------------ #
    def remove_all_excluded_hosts(
        self,
        comment: str,
        network_id: str | None = None,
        confirm: str | None = None,
    ) -> dict[str, Any]:
        """Remove ALL hosts from the excluded-hosts list in one call. IRREVERSIBLE.

        This clears the entire excluded-hosts list (or the list for
        ``network_id`` when specified) rather than a targeted subset, so it is
        treated as destructive even though the Qualys docs classify it as a
        routine "manage" action. Re-establishing the prior exclusion set
        requires re-adding every IP manually.

        Args:
            comment: User-defined notes (up to 1024 characters).
            network_id: Network ID whose excluded IPs should be cleared (only
                valid when the caller has access to more than one network;
                defaults to the caller's default network).
            confirm: Must equal the literal string ``"ALL"`` to proceed.

        Returns:
            SIMPLE_RETURN confirming the list was cleared, or a
            confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected="ALL")
        if guard:
            return guard
        data = {
            "action": "remove_all",
            "comment": comment,
            "network_id": network_id,
        }
        return self._fo("/api/2.0/fo/asset/excluded_ip/", method="POST", data=data)
