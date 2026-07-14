"""Policy Compliance — Compliance Policies module (classic FO + PCAS gateway).

Covers listing, exporting, importing, and merging compliance policies, plus
managing the asset tags/groups assigned to a policy (all classic FO,
``/api/2.0/fo/compliance/policy/``), and top-level policy update/delete (PCAS
gateway API, ``/pcas/v3/policy``, JWT bearer auth) since the classic FO API has
no direct "update policy fields" or "delete policy" action.

Docs: Qualys VM/PC API User Guide — "Compliance Policy List/Export/Import/
Merge/Manage Asset Tags/Manage Asset Groups"; PCAS Policy API ("Policy").
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class PcPoliciesModule(BaseModule):
    """Manage Policy Compliance (PC) compliance policies."""

    module_label = "pc_policies"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(server, self.list_compliance_policies, "list_compliance_policies", tier="read")
        self._add_tool(server, self.export_compliance_policy, "export_compliance_policy", tier="read")
        # Writes
        self._add_tool(server, self.import_compliance_policy, "import_compliance_policy", tier="write")
        self._add_tool(server, self.merge_compliance_policy, "merge_compliance_policy", tier="write")
        self._add_tool(server, self.manage_policy_asset_tags, "manage_policy_asset_tags", tier="write")
        self._add_tool(server, self.manage_policy_asset_groups, "manage_policy_asset_groups", tier="write")
        self._add_tool(server, self.update_compliance_policy, "update_compliance_policy", tier="write")
        # Destructive
        self._add_tool(server, self.delete_compliance_policy, "delete_compliance_policy", tier="destructive")

    # ------------------------------------------------------------------ #
    # Reads
    # ------------------------------------------------------------------ #
    def list_compliance_policies(
        self,
        details: str = "Basic",
        ids: str | None = None,
        id_min: int | None = None,
        id_max: int | None = None,
        updated_after_datetime: str | None = None,
        created_after_datetime: str | None = None,
        echo_request: bool | None = None,
    ) -> dict[str, Any]:
        """List compliance policies visible to the user.

        Args:
            details: Level of detail — "None" (ID only), "Basic" (default:
                title, created/modified dates, asset groups/tags, controls,
                Evaluate Now flag, lock status, glossary), or "All" (Basic
                plus technology list per control, IP list per asset group,
                and user list).
            ids: Comma-separated policy IDs and/or ID ranges (e.g. "160-165").
            id_min: Lower bound policy ID for a range query.
            id_max: Upper bound policy ID for a range query.
            updated_after_datetime: ISO date/time (YYYY-MM-DD[THH:MM:SSZ]) —
                only policies updated after this.
            created_after_datetime: ISO date/time — only policies created
                after this.
            echo_request: Echo the request's input parameters in the output.

        Returns:
            Parsed POLICY_LIST_OUTPUT.
        """
        params = {
            "action": "list",
            "details": details,
            "ids": ids,
            "id_min": id_min,
            "id_max": id_max,
            "updated_after_datetime": updated_after_datetime,
            "created_after_datetime": created_after_datetime,
            "echo_request": echo_request,
        }
        return self._fo("/api/2.0/fo/compliance/policy/", method="GET", params=params)

    def export_compliance_policy(
        self,
        id: int | None = None,
        title: str | None = None,
        show_user_controls: bool | None = None,
        show_appendix: bool | None = None,
    ) -> dict[str, Any]:
        """Export a compliance policy to XML (service-provided controls, optionally UDCs).

        Provide exactly one of ``id`` or ``title`` to select the policy.

        Args:
            id: ID of the policy to export.
            title: Title of the policy to export (alternative to ``id``).
            show_user_controls: Include user-defined controls (UDCs) in the
                output, with their UDC IDs.
            show_appendix: Include the appendix section with human-readable
                lookups for control descriptions. Note: an exported file with
                the appendix cannot be re-imported as-is (remove it first).

        Returns:
            Parsed POLICY_EXPORT_OUTPUT.
        """
        params = {
            "action": "export",
            "id": id,
            "title": title,
            "show_user_controls": show_user_controls,
            "show_appendix": show_appendix,
        }
        return self._fo("/api/2.0/fo/compliance/policy/", method="GET", params=params)

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #
    def import_compliance_policy(
        self,
        title: str,
        policy_xml: str,
        create_user_controls: bool | None = None,
    ) -> dict[str, Any]:
        """Import a compliance policy defined in XML into the account.

        Args:
            title: Title for the new policy.
            policy_xml: The policy XML content (the same document you would
                otherwise upload via ``curl --data-binary @policy.xml``).
            create_user_controls: Also create user-defined controls (UDCs)
                found in the XML. When not set, UDCs in the file are ignored.

        Returns:
            SIMPLE_RETURN with the new policy ID/title, or an error dict.

        Note:
            Qualys expects the policy XML as the raw POST body (Content-Type:
            text/xml) with ``action``/``title`` as query parameters — e.g.
            ``curl --data-binary @policy.xml
            ".../policy/?action=import&title=My+Policy"``. Sent via
            ``self._fo()``'s raw-body passthrough (content=/content_type=)
            rather than a form field.
        """
        # Raw-body requirement: the policy XML must be the verbatim POST
        # body, not a form-encoded field — action/title stay in params=.
        params = {
            "action": "import",
            "title": title,
            "create_user_controls": create_user_controls,
        }
        return self._fo(
            "/api/2.0/fo/compliance/policy/",
            method="POST",
            params=params,
            content=policy_xml,
            content_type="text/xml",
        )

    def merge_compliance_policy(
        self,
        id: int,
        merge_policy_id: int,
        replace_cover_page: bool | None = None,
        replace_asset_groups: bool | None = None,
        add_new_asset_groups: bool | None = None,
        add_new_technologies: bool | None = None,
        add_new_controls: bool | None = None,
        update_section_heading: bool | None = None,
        update_existing_controls: bool | None = None,
        preview_merge: bool | None = None,
    ) -> dict[str, Any]:
        """Merge one compliance policy's content into another.

        Merges content from a source policy ("Policy B") into a target
        policy ("Policy A") without losing Policy A's own customizations,
        unless no options are specified (in which case nothing changes).

        Args:
            id: ID of the policy to be updated with merged content (Policy A).
            merge_policy_id: ID of the policy providing the merge content
                (Policy B).
                # TODO(verify): The API also accepts raw policy XML in place
                of ``merge_policy_id`` (mutually exclusive, uploaded as the
                raw POST body). That variant is not supported here because
                the shared ``self._fo()`` wrapper has no raw-body passthrough.
            replace_cover_page: Replace Policy A's cover page with Policy B's.
            replace_asset_groups: Replace Policy A's asset groups with Policy
                B's. Mutually exclusive with ``add_new_asset_groups``.
            add_new_asset_groups: Add asset groups from Policy B not already
                in Policy A. Mutually exclusive with ``replace_asset_groups``.
            add_new_technologies: Add technologies from Policy B not already
                in Policy A (and apply them to relevant existing controls).
            add_new_controls: Add controls from Policy B not already in
                Policy A.
            update_section_heading: Replace common section headings in Policy
                A with Policy B's (by section number). Must be combined with
                ``add_new_controls`` or ``update_existing_controls``.
            update_existing_controls: Replace controls common to both
                policies with Policy B's versions (status, criticality,
                reference text, evaluation operator/value, fixed values).
            preview_merge: Preview the merged result without saving changes.

        Returns:
            Parsed POLICY_MERGE_RESULT_OUTPUT, or an error dict.
        """
        data = {
            "action": "merge",
            "id": id,
            "merge_policy_id": merge_policy_id,
            "replace_cover_page": replace_cover_page,
            "replace_asset_groups": replace_asset_groups,
            "add_new_asset_groups": add_new_asset_groups,
            "add_new_technologies": add_new_technologies,
            "add_new_controls": add_new_controls,
            "update_section_heading": update_section_heading,
            "update_existing_controls": update_existing_controls,
            "preview_merge": preview_merge,
        }
        return self._fo("/api/2.0/fo/compliance/policy/", method="POST", data=data)

    def manage_policy_asset_tags(
        self,
        id: int,
        operation: str,
        evaluate_now: bool | None = None,
        tag_include_selector: str | None = None,
        tag_exclude_selector: str | None = None,
        tag_set_by: str | None = None,
        tag_set_include: str | None = None,
        tag_set_exclude: str | None = None,
    ) -> dict[str, Any]:
        """Add, remove, or set the asset tags assigned to a compliance policy.

        Args:
            id: Policy ID to update.
            operation: One of "add", "remove", "set" — maps to the
                add_asset_tags/remove_asset_tags/set_asset_tags actions.
            evaluate_now: Immediately evaluate the policy against assigned
                assets after the change (also sets the "Evaluate Now"
                checkbox in the UI Policy Editor).
            tag_include_selector: "any" (default) to include hosts matching
                at least one selected tag, or "all" to require all of them.
            tag_exclude_selector: "any" (default) or "all" — same semantics
                for excluded tags.
            tag_set_by: "id" (default) to select tags by ID, or "name" to
                select by tag name.
            tag_set_include: Comma-separated tag IDs/names to include.
            tag_set_exclude: Comma-separated tag IDs/names to exclude.

        Returns:
            SIMPLE_RETURN status, or an error dict.
        """
        operation = operation.lower().strip()
        if operation not in ("add", "remove", "set"):
            return {"error": "operation must be one of: add, remove, set"}
        data = {
            "action": f"{operation}_asset_tags",
            "id": id,
            "evaluate_now": evaluate_now,
            "tag_include_selector": tag_include_selector,
            "tag_exclude_selector": tag_exclude_selector,
            "tag_set_by": tag_set_by,
            "tag_set_include": tag_set_include,
            "tag_set_exclude": tag_set_exclude,
        }
        return self._fo("/api/2.0/fo/compliance/policy/", method="POST", data=data)

    def manage_policy_asset_groups(
        self,
        id: int,
        operation: str,
        asset_group_ids: str,
        evaluate_now: bool | None = None,
    ) -> dict[str, Any]:
        """Add, remove, or set the asset groups assigned to a compliance policy.

        Args:
            id: Policy ID to update.
            operation: One of "add", "remove", "set" — maps to the
                add_asset_group_ids/remove_asset_group_ids/set_asset_group_ids
                actions. "set" replaces the full asset group assignment;
                groups not listed are removed.
            asset_group_ids: Comma-separated asset group IDs. Each group must
                have at least one assigned IP address.
            evaluate_now: Immediately evaluate the policy against assigned
                assets after the change.

        Returns:
            SIMPLE_RETURN status, or an error dict.
        """
        operation = operation.lower().strip()
        if operation not in ("add", "remove", "set"):
            return {"error": "operation must be one of: add, remove, set"}
        data = {
            "action": f"{operation}_asset_group_ids",
            "id": id,
            "asset_group_ids": asset_group_ids,
            "evaluate_now": evaluate_now,
        }
        return self._fo("/api/2.0/fo/compliance/policy/", method="POST", data=data)

    def update_compliance_policy(
        self,
        policy_id: int,
        policy_title: str | None = None,
        cover_page: str | None = None,
        is_active: bool | None = None,
    ) -> dict[str, Any]:
        """Update a compliance policy's title, cover page, and/or active status.

        Uses the PCAS Policy API since the classic FO API has no direct action
        for updating these top-level policy fields (only export/import/merge/
        asset associations).

        Args:
            policy_id: ID of the policy to update.
            policy_title: New title for the policy.
            cover_page: Replacement cover page text.
            is_active: True to activate the policy, False to deactivate it.

        Returns:
            Empty dict on success (HTTP 204 has no body), or an error dict.

        Note:
            # TODO(verify): This module reaches PCAS (``/pcas/v3/...``) via
            ``self._gateway()`` (JWT Bearer on the configured gateway host).
            Some doc samples show PCAS reached via the classic API host
            instead. Confirm the correct host for your platform.
        """
        body: dict[str, Any] = {"policyId": policy_id}
        if policy_title is not None:
            body["policyTitle"] = policy_title
        if cover_page is not None:
            body["coverPage"] = cover_page
        if is_active is not None:
            body["isActive"] = is_active
        return self._gateway("/pcas/v3/policy", method="PUT", json=body)

    # ------------------------------------------------------------------ #
    # Destructive
    # ------------------------------------------------------------------ #
    def delete_compliance_policy(self, policy_id: int, confirm: str | None = None) -> dict[str, Any]:
        """Permanently delete a compliance policy, its exceptions, and posture data. IRREVERSIBLE.

        Uses the PCAS Policy API. Only Manager and Auditor users can delete a
        policy, and only one policy can be deleted per call.

        Args:
            policy_id: ID of the policy to delete.
            confirm: Must equal ``str(policy_id)`` to proceed.

        Returns:
            Empty dict on success (HTTP 204 has no body), or a
            confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=str(policy_id))
        if guard:
            return guard
        return self._gateway("/pcas/v3/policy", method="DELETE", params={"policyId": policy_id})
