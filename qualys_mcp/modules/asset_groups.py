"""Asset Groups module (classic FO API) — organize hosts into scan-able groups.

Covers:
* Asset Group List (``/api/2.0/fo/asset/group/`` action=list).
* Add/Edit Asset Group (``/api/2.0/fo/asset/group/`` action=add|edit).
* Delete Asset Group (``/api/2.0/fo/asset/group/`` action=delete) — DESTRUCTIVE.

Docs: Qualys VM/PC API User Guide — "Assets" chapter ("Asset Group List",
"Manage Asset Groups").
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class AssetGroupsModule(BaseModule):
    """List, create, edit, and delete asset groups."""

    module_label = "asset_groups"

    def register_tools(self, server: FastMCP) -> None:
        self._add_tool(server, self.list_asset_groups, "list_asset_groups", tier="read")
        self._add_tool(server, self.add_asset_group, "add_asset_group", tier="write")
        self._add_tool(server, self.edit_asset_group, "edit_asset_group", tier="write")
        self._add_tool(
            server, self.delete_asset_group, "delete_asset_group", tier="destructive"
        )

    # ------------------------------------------------------------------ #
    # Reads
    # ------------------------------------------------------------------ #
    def list_asset_groups(
        self,
        ids: str | None = None,
        id_min: int | None = None,
        id_max: int | None = None,
        title: str | None = None,
        network_ids: str | None = None,
        unit_id: str | None = None,
        user_id: str | None = None,
        show_attributes: str | None = None,
        truncation_limit: int | None = None,
        output_format: str = "xml",
        echo_request: bool | None = None,
    ) -> dict[str, Any]:
        """List asset groups in the user account.

        Args:
            ids: Comma-separated asset group IDs to restrict the list to.
            id_min: Minimum asset group ID (inclusive).
            id_max: Maximum asset group ID (inclusive).
            title: Exact-match asset group title.
            network_ids: Comma-separated custom network IDs (Networks feature only).
            unit_id: Restrict to asset groups owned by this business unit ID.
            user_id: Restrict to asset groups owned by this user ID.
            show_attributes: "ALL" or a comma-separated list of attribute names to
                include: ID, TITLE, OWNER_USER_NAME, OWNER_USER_ID, OWNER_UNIT_ID,
                NETWORK_IDS, LAST_UPDATE, IP_SET, APPLIANCE_LIST, DOMAIN_LIST,
                DNS_LIST, NETBIOS_LIST, EC2_ID_LIST, HOST_IDS, ASSIGNED_USER_IDS,
                ASSIGNED_UNIT_IDS, BUSINESS_IMPACT, CVSS, COMMENTS.
            truncation_limit: Max asset group records per page (default 1000; 0 =
                no limit).
            output_format: "xml" (default) or "csv". Qualys only accepts lowercase.
            echo_request: Echo input parameters back in the output.

        Returns:
            Parsed ASSET_GROUP_LIST_OUTPUT, or ``{"raw": ...}`` for CSV.
        """
        params = {
            "action": "list",
            "ids": ids,
            "id_min": id_min,
            "id_max": id_max,
            "title": title,
            "network_ids": network_ids,
            "unit_id": unit_id,
            "user_id": user_id,
            "show_attributes": show_attributes,
            "truncation_limit": truncation_limit,
            "output_format": output_format.lower(),
            "echo_request": echo_request,
        }
        parse = output_format.lower() == "xml"
        return self._fo("/api/2.0/fo/asset/group/", method="GET", params=params, parse=parse)

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #
    def add_asset_group(
        self,
        title: str,
        network_id: str | None = None,
        ips: str | None = None,
        appliance_ids: str | None = None,
        default_appliance_id: str | None = None,
        domains: str | None = None,
        dns_names: str | None = None,
        netbios_names: str | None = None,
        comments: str | None = None,
        division: str | None = None,
        function: str | None = None,
        location: str | None = None,
        business_impact: str | None = None,
        cvss_enviro_cdp: str | None = None,
        cvss_enviro_td: str | None = None,
        cvss_enviro_cr: str | None = None,
        cvss_enviro_ir: str | None = None,
        cvss_enviro_ar: str | None = None,
        echo_request: bool | None = None,
    ) -> dict[str, Any]:
        """Create a new asset group.

        Args:
            title: Asset group title. Must be unique and cannot be "All".
            network_id: Network ID to assign the group to (Networks feature only).
            ips: Comma-separated IPs/ranges to seed the group with.
            appliance_ids: Comma-separated scanner appliance IDs to assign to the group.
            default_appliance_id: Default scanner appliance ID for the group.
            domains: Comma-separated domains to seed the group with.
            dns_names: Comma-separated DNS hostnames to seed the group with.
            netbios_names: Comma-separated NetBIOS hostnames to seed the group with.
            comments: User-defined comments (max 255 chars).
            division: Division name (max 64 chars).
            function: Business function name (max 64 chars).
            location: Location name (max 64 chars).
            business_impact: One of "critical", "high", "medium", "low", "none".
            cvss_enviro_cdp: CVSS environmental Collateral Damage Potential: "high",
                "medium-high", "low-medium", "low", "none".
            cvss_enviro_td: CVSS environmental Target Distribution: "high", "medium",
                "low", "none".
            cvss_enviro_cr: CVSS environmental Confidentiality Requirement: "high",
                "medium", "low".
            cvss_enviro_ir: CVSS environmental Integrity Requirement: "high", "medium", "low".
            cvss_enviro_ar: CVSS environmental Availability Requirement: "high", "medium", "low".
            echo_request: Echo input parameters back in the output.

        Returns:
            SIMPLE_RETURN with the new asset group ID (``ITEM_LIST`` key "ID"), or
            an error dict.
        """
        data = {
            "action": "add",
            "title": title,
            "network_id": network_id,
            "ips": ips,
            "appliance_ids": appliance_ids,
            "default_appliance_id": default_appliance_id,
            "domains": domains,
            "dns_names": dns_names,
            "netbios_names": netbios_names,
            "comments": comments,
            "division": division,
            "function": function,
            "location": location,
            "business_impact": business_impact,
            "cvss_enviro_cdp": cvss_enviro_cdp,
            "cvss_enviro_td": cvss_enviro_td,
            "cvss_enviro_cr": cvss_enviro_cr,
            "cvss_enviro_ir": cvss_enviro_ir,
            "cvss_enviro_ar": cvss_enviro_ar,
            "echo_request": echo_request,
        }
        return self._fo("/api/2.0/fo/asset/group/", method="POST", data=data)

    def edit_asset_group(
        self,
        id: str,
        set_title: str | None = None,
        add_ips: str | None = None,
        remove_ips: str | None = None,
        set_ips: str | None = None,
        add_appliance_ids: str | None = None,
        remove_appliance_ids: str | None = None,
        set_appliance_ids: str | None = None,
        set_default_appliance_id: str | None = None,
        add_domains: str | None = None,
        remove_domains: str | None = None,
        set_domains: str | None = None,
        add_dns_names: str | None = None,
        remove_dns_names: str | None = None,
        set_dns_names: str | None = None,
        add_netbios_names: str | None = None,
        remove_netbios_names: str | None = None,
        set_netbios_names: str | None = None,
        set_comments: str | None = None,
        set_division: str | None = None,
        set_function: str | None = None,
        set_location: str | None = None,
        set_business_impact: str | None = None,
        set_cvss_enviro_cdp: str | None = None,
        set_cvss_enviro_td: str | None = None,
        set_cvss_enviro_cr: str | None = None,
        set_cvss_enviro_ir: str | None = None,
        set_cvss_enviro_ar: str | None = None,
        echo_request: bool | None = None,
    ) -> dict[str, Any]:
        """Edit an existing asset group.

        For list-valued attributes (IPs, appliance IDs, domains, DNS names,
        NetBIOS names) use ``add_*``/``remove_*`` to incrementally modify the
        existing list, or ``set_*`` to overwrite it entirely. A ``set_*`` call
        can leave the group with no entries for that attribute if given an
        empty value.

        Args:
            id: The ID of the asset group to edit.
            set_title: Overwrite the asset group title (max 255 chars).
            add_ips: Comma-separated IPs/ranges to add.
            remove_ips: Comma-separated IPs/ranges to remove.
            set_ips: Comma-separated IPs/ranges to overwrite the group's IP set with.
            add_appliance_ids: Comma-separated scanner appliance IDs to add.
            remove_appliance_ids: Comma-separated scanner appliance IDs to remove.
            set_appliance_ids: Comma-separated scanner appliance IDs to overwrite with.
            set_default_appliance_id: Overwrite the default scanner appliance ID.
            add_domains: Comma-separated domains to add.
            remove_domains: Comma-separated domains to remove.
            set_domains: Comma-separated domains to overwrite with.
            add_dns_names: Comma-separated DNS hostnames to add.
            remove_dns_names: Comma-separated DNS hostnames to remove.
            set_dns_names: Comma-separated DNS hostnames to overwrite with.
            add_netbios_names: Comma-separated NetBIOS hostnames to add.
            remove_netbios_names: Comma-separated NetBIOS hostnames to remove.
            set_netbios_names: Comma-separated NetBIOS hostnames to overwrite with.
            set_comments: Overwrite user-defined comments (max 255 chars).
            set_division: Overwrite division name (max 64 chars).
            set_function: Overwrite business function name (max 64 chars).
            set_location: Overwrite location name (max 64 chars).
            set_business_impact: One of "critical", "high", "medium", "low", "none".
            set_cvss_enviro_cdp: "high", "medium-high", "low-medium", "low", "none".
            set_cvss_enviro_td: "high", "medium", "low", "none".
            set_cvss_enviro_cr: "high", "medium", "low".
            set_cvss_enviro_ir: "high", "medium", "low".
            set_cvss_enviro_ar: "high", "medium", "low".
            echo_request: Echo input parameters back in the output.

        Returns:
            SIMPLE_RETURN confirming the update, or an error dict.
        """
        data = {
            "action": "edit",
            "id": id,
            "set_title": set_title,
            "add_ips": add_ips,
            "remove_ips": remove_ips,
            "set_ips": set_ips,
            "add_appliance_ids": add_appliance_ids,
            "remove_appliance_ids": remove_appliance_ids,
            "set_appliance_ids": set_appliance_ids,
            "set_default_appliance_id": set_default_appliance_id,
            "add_domains": add_domains,
            "remove_domains": remove_domains,
            "set_domains": set_domains,
            "add_dns_names": add_dns_names,
            "remove_dns_names": remove_dns_names,
            "set_dns_names": set_dns_names,
            "add_netbios_names": add_netbios_names,
            "remove_netbios_names": remove_netbios_names,
            "set_netbios_names": set_netbios_names,
            "set_comments": set_comments,
            "set_division": set_division,
            "set_function": set_function,
            "set_location": set_location,
            "set_business_impact": set_business_impact,
            "set_cvss_enviro_cdp": set_cvss_enviro_cdp,
            "set_cvss_enviro_td": set_cvss_enviro_td,
            "set_cvss_enviro_cr": set_cvss_enviro_cr,
            "set_cvss_enviro_ir": set_cvss_enviro_ir,
            "set_cvss_enviro_ar": set_cvss_enviro_ar,
            "echo_request": echo_request,
        }
        return self._fo("/api/2.0/fo/asset/group/", method="POST", data=data)

    # ------------------------------------------------------------------ #
    # Destructive
    # ------------------------------------------------------------------ #
    def delete_asset_group(
        self, id: str, confirm: str | None = None
    ) -> dict[str, Any]:
        """Permanently delete an asset group. IRREVERSIBLE.

        Deleting an asset group deactivates any scheduled scans that use it.

        Args:
            id: The ID of the asset group to delete.
            confirm: Must equal ``id`` to proceed.

        Returns:
            SIMPLE_RETURN confirming deletion, or a confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=id)
        if guard:
            return guard
        data = {"action": "delete", "id": id}
        return self._fo("/api/2.0/fo/asset/group/", method="POST", data=data)
