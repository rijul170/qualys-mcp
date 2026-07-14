"""Search Lists module (classic FO API).

Covers static search lists (explicit QID membership) and dynamic search
lists (QID membership derived from filter criteria evaluated against the
KnowledgeBase). Dynamic search list criteria has dozens of possible filter
fields; the most commonly used ones are exposed here rather than every field
— see ``# TODO(verify)`` markers for gaps.

Endpoints:
* ``/api/2.0/fo/qid/search_list/static/``
* ``/api/2.0/fo/qid/search_list/dynamic/``

Docs: Qualys VM/PC API User Guide — "Static Search Lists", "Dynamic Search
Lists".
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class SearchListsModule(BaseModule):
    """Create and manage static and dynamic QID search lists."""

    module_label = "search_lists"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(
            server, self.list_static_search_lists, "list_static_search_lists", tier="read"
        )
        self._add_tool(
            server, self.list_dynamic_search_lists, "list_dynamic_search_lists", tier="read"
        )
        # Writes
        self._add_tool(
            server, self.create_static_search_list, "create_static_search_list", tier="write"
        )
        self._add_tool(
            server, self.update_static_search_list, "update_static_search_list", tier="write"
        )
        self._add_tool(
            server, self.create_dynamic_search_list, "create_dynamic_search_list", tier="write"
        )
        self._add_tool(
            server, self.update_dynamic_search_list, "update_dynamic_search_list", tier="write"
        )
        # Destructive
        self._add_tool(
            server, self.delete_static_search_list, "delete_static_search_list", tier="destructive"
        )
        self._add_tool(
            server, self.delete_dynamic_search_list, "delete_dynamic_search_list", tier="destructive"
        )

    # ------------------------------------------------------------------ #
    # Static search lists — reads
    # ------------------------------------------------------------------ #
    def list_static_search_lists(self, ids: str | None = None) -> dict[str, Any]:
        """List static search lists.

        Args:
            ids: Comma-separated search list IDs to restrict output to. When
                omitted, all static search lists are returned.

        Returns:
            Parsed STATIC_SEARCH_LIST_OUTPUT, including associated option
            profiles, report templates, remediation policies, and
            distribution groups for each list.
        """
        params = {"action": "list", "ids": ids}
        return self._fo("/api/2.0/fo/qid/search_list/static/", method="GET", params=params)

    # ------------------------------------------------------------------ #
    # Static search lists — writes
    # ------------------------------------------------------------------ #
    def create_static_search_list(
        self,
        title: str,
        qids: str,
        global_list: bool | None = None,
        comments: str | None = None,
    ) -> dict[str, Any]:
        """Create a static search list from an explicit QID set.

        Args:
            title: User-defined title, max 256 ASCII characters.
            qids: Comma-separated QIDs/ranges to include (e.g.
                "68518-68522,48000").
            global_list: Make this list available to all subscription users.
            comments: User-defined comments.

        Returns:
            SIMPLE_RETURN status with the new search list ID, or an error
            dict.
        """
        data = {
            "action": "create",
            "title": title,
            "qids": qids,
            "global": global_list,
            "comments": comments,
        }
        return self._fo("/api/2.0/fo/qid/search_list/static/", method="POST", data=data)

    def update_static_search_list(
        self,
        search_list_id: int,
        title: str | None = None,
        qids: str | None = None,
        add_qids: str | None = None,
        remove_qids: str | None = None,
        global_list: bool | None = None,
        comments: str | None = None,
    ) -> dict[str, Any]:
        """Update a static search list's title, membership, or comments.

        Args:
            search_list_id: ID of the static search list to update.
            title: New title, max 256 ASCII characters.
            qids: Comma-separated QIDs/ranges that *replace* all existing
                membership. Mutually exclusive with add_qids/remove_qids.
            add_qids: Comma-separated QIDs/ranges to add to existing
                membership. Mutually exclusive with qids.
            remove_qids: Comma-separated QIDs/ranges to remove from existing
                membership. Mutually exclusive with qids.
            global_list: Make this list available to all subscription users.
            comments: User-defined comments.

        Returns:
            SIMPLE_RETURN status, or an error dict.
        """
        data = {
            "action": "update",
            "id": search_list_id,
            "title": title,
            "qids": qids,
            "add_qids": add_qids,
            "remove_qids": remove_qids,
            "global": global_list,
            "comments": comments,
        }
        return self._fo("/api/2.0/fo/qid/search_list/static/", method="POST", data=data)

    # ------------------------------------------------------------------ #
    # Static search lists — destructive
    # ------------------------------------------------------------------ #
    def delete_static_search_list(
        self, search_list_id: int, confirm: str | None = None
    ) -> dict[str, Any]:
        """Permanently delete a static search list. IRREVERSIBLE.

        Args:
            search_list_id: ID of the static search list to delete.
            confirm: Must equal ``str(search_list_id)`` to proceed.

        Returns:
            SIMPLE_RETURN status, or a confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=str(search_list_id))
        if guard:
            return guard
        data = {"action": "delete", "id": search_list_id}
        return self._fo("/api/2.0/fo/qid/search_list/static/", method="POST", data=data)

    # ------------------------------------------------------------------ #
    # Dynamic search lists — reads
    # ------------------------------------------------------------------ #
    def list_dynamic_search_lists(
        self,
        ids: str | None = None,
        show_qids: bool | None = None,
        show_option_profiles: bool | None = None,
        show_distribution_groups: bool | None = None,
        show_report_templates: bool | None = None,
        show_remediation_policies: bool | None = None,
    ) -> dict[str, Any]:
        """List dynamic search lists.

        Args:
            ids: Comma-separated search list IDs to restrict output to. When
                omitted, all dynamic search lists are returned.
            show_qids: Show QIDs currently matching each list's criteria
                (default True; set False to hide).
            show_option_profiles: Show option profiles that reference each
                list (default True; set False to hide).
            show_distribution_groups: Show distribution groups that reference
                each list (default True; set False to hide).
            show_report_templates: Show report templates that reference each
                list (default True; set False to hide).
            show_remediation_policies: Show remediation policies that
                reference each list (default True; set False to hide).

        Returns:
            Parsed DYNAMIC_SEARCH_LIST_OUTPUT, including each list's CRITERIA.
        """
        params = {
            "action": "list",
            "ids": ids,
            "show_qids": show_qids,
            "show_option_profiles": show_option_profiles,
            "show_distribution_groups": show_distribution_groups,
            "show_report_templates": show_report_templates,
            "show_remediation_policies": show_remediation_policies,
        }
        return self._fo("/api/2.0/fo/qid/search_list/dynamic/", method="GET", params=params)

    # ------------------------------------------------------------------ #
    # Dynamic search lists — writes
    # ------------------------------------------------------------------ #
    def create_dynamic_search_list(
        self,
        title: str,
        global_list: bool | None = None,
        comments: str | None = None,
        vuln_title: str | None = None,
        discovery_methods: str | None = None,
        auth_types: str | None = None,
        categories: str | None = None,
        confirmed_severities: str | None = None,
        potential_severities: str | None = None,
        ig_severities: str | None = None,
        vendor_ids: str | None = None,
        products: str | None = None,
        patch_available: str | None = None,
        cve_ids: str | None = None,
        cve_ids_filter: int | None = None,
        cvss_base: float | None = None,
        cvss_base_operand: int | None = None,
        cvss_temp: float | None = None,
        cvss_temp_operand: int | None = None,
        cvss3_base: float | None = None,
        cvss3_base_operand: int | None = None,
        cvss3_temp: float | None = None,
        cvss3_temp_operand: int | None = None,
        published_date_within_last_days: int | None = None,
    ) -> dict[str, Any]:
        """Create a dynamic search list from filter criteria.

        At least one criteria parameter must be provided. Every criteria
        parameter is a filter that narrows which KnowledgeBase QIDs belong to
        the list; unspecified filters are not applied.

        # TODO(verify): the API supports many more criteria fields not
        # exposed here: not_vuln_title, not_categories, not_vendor_ids,
        # not_products, virtual_patch_available, not_cve_ids, exploitability,
        # malware_associated, vendor_refs, not_vendor_refs, bugtraq_id,
        # not_bugtraq_id, vuln_details, compliance_details,
        # supported_modules, compliance_types, qualys_top_lists, cpe,
        # qids_not_exploitable, non_running_services, sans_20, nac_nam,
        # vuln_provider, user_modified_date_*, service_modified_date_*,
        # published_date_between/today/in_previous, not_published,
        # cloud_agent_scan_type. Use export/import for full control.

        Args:
            title: User-defined title, max 256 ASCII characters.
            global_list: Make this list available to all subscription users.
            comments: User-defined comments.
            vuln_title: Filter by vulnerability title (string match).
            discovery_methods: One or more of "Remote", "Authenticated",
                "Remote_Authenticated" (comma separated). Default: all.
            auth_types: One or more of "Windows", "Unix", "Oracle", "SNMP",
                "VMware", "DB2", "HTTP", "MySQL", "PANOS", "TOMCAT",
                "MARIADB", "MongoDB", "WEBLOGIC" (comma separated).
            categories: One or more vulnerability category names (comma
                separated).
            confirmed_severities: One or more confirmed-vuln severities 1-5
                (comma separated).
            potential_severities: One or more potential-vuln severities 1-5
                (comma separated).
            ig_severities: One or more information-gathered severities 1-5
                (comma separated).
            vendor_ids: One or more vendor IDs (comma separated; see
                KnowledgeBaseModule.list_vendor_references' sibling
                list_vendors action for IDs).
            products: One or more vendor product names (comma separated).
            patch_available: "0" (no patch) and/or "1" (patch available),
                comma separated. Default: both.
            cve_ids: One or more CVE IDs (comma separated).
            cve_ids_filter: 1 for exact match, 2 for "contains" match against
                cve_ids.
            cvss_base: CVSS v2 base score threshold.
            cvss_base_operand: 1 for ">=" or 2 for "<" against cvss_base.
                Required whenever cvss_base is set.
            cvss_temp: CVSS v2 temporal score threshold.
            cvss_temp_operand: 1 for ">=" or 2 for "<" against cvss_temp.
                Required whenever cvss_temp is set.
            cvss3_base: CVSS v3 base score threshold.
            cvss3_base_operand: 1 for ">=" or 2 for "<" against cvss3_base.
                Required whenever cvss3_base is set.
            cvss3_temp: CVSS v3 temporal score threshold.
            cvss3_temp_operand: 1 for ">=" or 2 for "<" against cvss3_temp.
                Required whenever cvss3_temp is set.
            published_date_within_last_days: Only QIDs published within this
                many days (1-9999).

        Returns:
            SIMPLE_RETURN status with the new search list ID, or an error
            dict.
        """
        data = {
            "action": "create",
            "title": title,
            "global": global_list,
            "comments": comments,
            "vuln_title": vuln_title,
            "discovery_methods": discovery_methods,
            "auth_types": auth_types,
            "categories": categories,
            "confirmed_severities": confirmed_severities,
            "potential_severities": potential_severities,
            "ig_severities": ig_severities,
            "vendor_ids": vendor_ids,
            "products": products,
            "patch_available": patch_available,
            "cve_ids": cve_ids,
            "cve_ids_filter": cve_ids_filter,
            "cvss_base": cvss_base,
            "cvss_base_operand": cvss_base_operand,
            "cvss_temp": cvss_temp,
            "cvss_temp_operand": cvss_temp_operand,
            "cvss3_base": cvss3_base,
            "cvss3_base_operand": cvss3_base_operand,
            "cvss3_temp": cvss3_temp,
            "cvss3_temp_operand": cvss3_temp_operand,
            "published_date_within_last_days": published_date_within_last_days,
        }
        return self._fo("/api/2.0/fo/qid/search_list/dynamic/", method="POST", data=data)

    def update_dynamic_search_list(
        self,
        search_list_id: int,
        title: str | None = None,
        global_list: bool | None = None,
        comments: str | None = None,
        vuln_title: str | None = None,
        discovery_methods: str | None = None,
        auth_types: str | None = None,
        categories: str | None = None,
        confirmed_severities: str | None = None,
        potential_severities: str | None = None,
        ig_severities: str | None = None,
        vendor_ids: str | None = None,
        products: str | None = None,
        patch_available: str | None = None,
        cve_ids: str | None = None,
        cve_ids_filter: int | None = None,
        cvss_base: float | None = None,
        cvss_base_operand: int | None = None,
        cvss_temp: float | None = None,
        cvss_temp_operand: int | None = None,
        cvss3_base: float | None = None,
        cvss3_base_operand: int | None = None,
        cvss3_temp: float | None = None,
        cvss3_temp_operand: int | None = None,
        published_date_within_last_days: int | None = None,
        unset_user_modified_date: bool = False,
        unset_published_date: bool = False,
        unset_service_modified_date: bool = False,
    ) -> dict[str, Any]:
        """Update a dynamic search list's title, criteria, or comments.

        Only criteria fields you pass are changed; each replaces the prior
        value for that field entirely (it does not merge with the existing
        filter). See ``create_dynamic_search_list`` for field semantics and
        the same "# TODO(verify)" field-coverage caveat.

        Args:
            search_list_id: ID of the dynamic search list to update.
            title: New title, max 256 ASCII characters.
            global_list: Make this list available to all subscription users.
            comments: User-defined comments.
            vuln_title: Filter by vulnerability title (pass "" to unset).
            discovery_methods: See ``create_dynamic_search_list`` (pass "" to
                unset).
            auth_types: See ``create_dynamic_search_list`` (pass "" to unset).
            categories: See ``create_dynamic_search_list`` (pass "" to unset).
            confirmed_severities: See ``create_dynamic_search_list`` (pass ""
                to unset).
            potential_severities: See ``create_dynamic_search_list`` (pass ""
                to unset).
            ig_severities: See ``create_dynamic_search_list`` (pass "" to
                unset).
            vendor_ids: See ``create_dynamic_search_list`` (pass "" to unset).
            products: See ``create_dynamic_search_list`` (pass "" to unset).
            patch_available: See ``create_dynamic_search_list`` (pass "" to
                unset).
            cve_ids: See ``create_dynamic_search_list`` (pass "" to unset).
            cve_ids_filter: 1 (exact) or 2 (contains) against cve_ids.
            cvss_base: CVSS v2 base score threshold (pass "" to unset).
            cvss_base_operand: 1 (">=") or 2 ("<") against cvss_base.
            cvss_temp: CVSS v2 temporal score threshold (pass "" to unset).
            cvss_temp_operand: 1 (">=") or 2 ("<") against cvss_temp.
            cvss3_base: CVSS v3 base score threshold (pass "" to unset).
            cvss3_base_operand: 1 (">=") or 2 ("<") against cvss3_base.
            cvss3_temp: CVSS v3 temporal score threshold (pass "" to unset).
            cvss3_temp_operand: 1 (">=") or 2 ("<") against cvss3_temp.
            published_date_within_last_days: Only QIDs published within this
                many days (1-9999).
            unset_user_modified_date: Clear the user-modified-date filter.
            unset_published_date: Clear the published-date filter.
            unset_service_modified_date: Clear the service-modified-date
                filter.

        Returns:
            SIMPLE_RETURN status, or an error dict.
        """
        data = {
            "action": "update",
            "id": search_list_id,
            "title": title,
            "global": global_list,
            "comments": comments,
            "vuln_title": vuln_title,
            "discovery_methods": discovery_methods,
            "auth_types": auth_types,
            "categories": categories,
            "confirmed_severities": confirmed_severities,
            "potential_severities": potential_severities,
            "ig_severities": ig_severities,
            "vendor_ids": vendor_ids,
            "products": products,
            "patch_available": patch_available,
            "cve_ids": cve_ids,
            "cve_ids_filter": cve_ids_filter,
            "cvss_base": cvss_base,
            "cvss_base_operand": cvss_base_operand,
            "cvss_temp": cvss_temp,
            "cvss_temp_operand": cvss_temp_operand,
            "cvss3_base": cvss3_base,
            "cvss3_base_operand": cvss3_base_operand,
            "cvss3_temp": cvss3_temp,
            "cvss3_temp_operand": cvss3_temp_operand,
            "published_date_within_last_days": published_date_within_last_days,
        }
        if unset_user_modified_date:
            data["unset_user_modified_date"] = ""
        if unset_published_date:
            data["unset_published_date"] = ""
        if unset_service_modified_date:
            data["unset_service_modified_date"] = ""
        return self._fo("/api/2.0/fo/qid/search_list/dynamic/", method="POST", data=data)

    # ------------------------------------------------------------------ #
    # Dynamic search lists — destructive
    # ------------------------------------------------------------------ #
    def delete_dynamic_search_list(
        self, search_list_id: int, confirm: str | None = None
    ) -> dict[str, Any]:
        """Permanently delete a dynamic search list. IRREVERSIBLE.

        Args:
            search_list_id: ID of the dynamic search list to delete.
            confirm: Must equal ``str(search_list_id)`` to proceed.

        Returns:
            SIMPLE_RETURN status, or a confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=str(search_list_id))
        if guard:
            return guard
        data = {"action": "delete", "id": search_list_id}
        return self._fo("/api/2.0/fo/qid/search_list/dynamic/", method="POST", data=data)
