"""Policy Compliance — PCAS Policies + Library module (Gateway/JWT REST API).

Covers the PCAS (Policy Compliance Automation Service) policy-authoring APIs
under ``/pcas/v3/policy...`` — export/update/delete, lock/unlock, and managing
technologies/sections/controls/evaluation criteria within a policy — plus the
PCAS Library APIs under ``/pcas/v1/library/...`` for browsing and importing
Qualys/vendor/CIS-style library policies. All of these are System Defined
Control (SDC) only; they do not support User Defined Controls (UDC).

Docs: Qualys VM/PC API User Guide — "PCAS Policies" (Policy, Lock Policy,
Policy Technology, Policy Section, Policy Section Control, Policy Section
Control Technology, Policy Section Control Technology Evaluate), "PCAS
Library Policy" (Library Label, Library Label Technology, Library Policy,
Library Policy Details, Import Library Policy).

Note:
    # TODO(verify): This module reaches PCAS via ``self._gateway()`` (JWT
    Bearer on the configured gateway host). Doc samples show these endpoints
    on both ``<qualys_base_url>`` and generic "Base URL" placeholders with
    Bearer-token auth; confirm the correct host for your platform.
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class PcasPoliciesModule(BaseModule):
    """Author Policy Compliance (PC) policies via the PCAS API, and browse the PCAS library."""

    module_label = "pcas_policies"

    def register_tools(self, server: FastMCP) -> None:
        # Policy (top-level)
        self._add_tool(server, self.get_pcas_policy, "get_pcas_policy", tier="read")
        self._add_tool(server, self.update_pcas_policy, "update_pcas_policy", tier="write")
        self._add_tool(server, self.lock_pcas_policy, "lock_pcas_policy", tier="write")
        self._add_tool(server, self.delete_pcas_policy, "delete_pcas_policy", tier="destructive")
        # Policy technology
        self._add_tool(server, self.list_pcas_policy_technologies, "list_pcas_policy_technologies", tier="read")
        self._add_tool(server, self.add_pcas_policy_technologies, "add_pcas_policy_technologies", tier="write")
        self._add_tool(server, self.remove_pcas_policy_technology, "remove_pcas_policy_technology", tier="write")
        # Policy section
        self._add_tool(server, self.get_pcas_policy_section, "get_pcas_policy_section", tier="read")
        self._add_tool(server, self.add_pcas_policy_section, "add_pcas_policy_section", tier="write")
        self._add_tool(server, self.update_pcas_policy_section, "update_pcas_policy_section", tier="write")
        self._add_tool(server, self.delete_pcas_policy_section, "delete_pcas_policy_section", tier="write")
        # Policy section control
        self._add_tool(server, self.get_pcas_policy_section_control, "get_pcas_policy_section_control", tier="read")
        self._add_tool(server, self.add_pcas_policy_section_control, "add_pcas_policy_section_control", tier="write")
        self._add_tool(
            server, self.update_pcas_policy_section_control, "update_pcas_policy_section_control", tier="write"
        )
        self._add_tool(
            server, self.delete_pcas_policy_section_control, "delete_pcas_policy_section_control", tier="write"
        )
        # Policy section control technology
        self._add_tool(server, self.list_pcas_control_technologies, "list_pcas_control_technologies", tier="read")
        self._add_tool(server, self.add_pcas_control_technologies, "add_pcas_control_technologies", tier="write")
        self._add_tool(server, self.remove_pcas_control_technology, "remove_pcas_control_technology", tier="write")
        # Policy section control technology evaluate
        self._add_tool(
            server,
            self.get_pcas_control_technology_evaluation,
            "get_pcas_control_technology_evaluation",
            tier="read",
        )
        self._add_tool(
            server,
            self.update_pcas_control_technology_evaluation,
            "update_pcas_control_technology_evaluation",
            tier="write",
        )
        # Library
        self._add_tool(server, self.list_pcas_library_labels, "list_pcas_library_labels", tier="read")
        self._add_tool(
            server, self.list_pcas_library_label_technologies, "list_pcas_library_label_technologies", tier="read"
        )
        self._add_tool(server, self.list_pcas_library_policies, "list_pcas_library_policies", tier="read")
        self._add_tool(server, self.get_pcas_library_policy, "get_pcas_library_policy", tier="read")
        self._add_tool(server, self.import_pcas_library_policy, "import_pcas_library_policy", tier="write")

    # ------------------------------------------------------------------ #
    # Policy
    # ------------------------------------------------------------------ #
    def get_pcas_policy(self, policy_id: int | None = None, policy_title: str | None = None) -> dict[str, Any]:
        """Export a compliance policy in JSON via the PCAS Policy API.

        Provide exactly one of ``policy_id`` or ``policy_title``.

        Args:
            policy_id: ID of the policy to export.
            policy_title: Title of the policy to export (URL-encode it
                yourself if it contains special characters).

        Returns:
            JSON policy document: policyId, policyTitle, exported, coverPage,
            isActive, isLocked, technologies, and sections (each with
            controls, and each control's technologies/evaluate/remediation).
        """
        params = {"policyId": policy_id, "policyTitle": policy_title}
        return self._gateway("/pcas/v3/policy", method="GET", params=params)

    def update_pcas_policy(
        self,
        policy_id: int,
        policy_title: str | None = None,
        cover_page: str | None = None,
        is_active: bool | None = None,
    ) -> dict[str, Any]:
        """Update a compliance policy's title, cover page, and/or active status.

        Remember to evaluate the policy after making changes.

        Args:
            policy_id: ID of the policy to update.
            policy_title: New title for the policy.
            cover_page: Replacement cover page text.
            is_active: True to activate the policy, False to deactivate it.

        Returns:
            Empty dict on success (HTTP 204 has no body), or an error dict.
        """
        body: dict[str, Any] = {"policyId": policy_id}
        if policy_title is not None:
            body["policyTitle"] = policy_title
        if cover_page is not None:
            body["coverPage"] = cover_page
        if is_active is not None:
            body["isActive"] = is_active
        return self._gateway("/pcas/v3/policy", method="PUT", json=body)

    def lock_pcas_policy(self, policy_id: int, is_locked: bool) -> dict[str, Any]:
        """Lock or unlock a compliance policy.

        Remember to evaluate the policy after making changes.

        Args:
            policy_id: ID of the policy to lock or unlock.
            is_locked: True to lock the policy (prevent edits), False to
                unlock it.

        Returns:
            Empty dict on success (HTTP 204 has no body), or an error dict.
        """
        body = {"policyId": policy_id, "isLocked": is_locked}
        return self._gateway("/pcas/v3/policy/lock", method="PUT", json=body)

    def delete_pcas_policy(self, policy_id: int, confirm: str | None = None) -> dict[str, Any]:
        """Permanently delete a compliance policy, its exceptions, and posture data. IRREVERSIBLE.

        Only Manager and Auditor users can delete a policy; only one policy
        can be deleted per call.

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

    # ------------------------------------------------------------------ #
    # Policy technology
    # ------------------------------------------------------------------ #
    def list_pcas_policy_technologies(self, policy_id: int) -> dict[str, Any]:
        """List all technologies associated with a compliance policy.

        Args:
            policy_id: ID of the policy to list technologies for.

        Returns:
            JSON ``{"policyId": ..., "technologies": [{"technologyId",
            "technologyName"}, ...]}``.
        """
        return self._gateway("/pcas/v3/policy/technology", method="GET", params={"policyId": policy_id})

    def add_pcas_policy_technologies(self, policy_id: int, technology_ids: str) -> dict[str, Any]:
        """Add technologies to a compliance policy (existing technologies are unaffected).

        Remember to evaluate the policy after making changes.

        Args:
            policy_id: ID of the policy to add technologies to.
            technology_ids: Comma-separated technology IDs to add.

        Returns:
            JSON list of the policy's technologies after the add.
        """
        body = {
            "policyId": policy_id,
            "technologyIds": [int(t) for t in technology_ids.split(",") if t.strip()],
        }
        return self._gateway("/pcas/v3/policy/technology", method="POST", json=body)

    def remove_pcas_policy_technology(self, policy_id: int, technology_id: int) -> dict[str, Any]:
        """Remove one technology from a compliance policy.

        Remember to evaluate the policy after making changes.

        Args:
            policy_id: ID of the policy to remove the technology from.
            technology_id: ID of the technology to remove.

        Returns:
            Empty dict on success (HTTP 204 has no body), or an error dict.
        """
        params = {"policyId": policy_id, "technologyId": technology_id}
        return self._gateway("/pcas/v3/policy/technology", method="DELETE", params=params)

    # ------------------------------------------------------------------ #
    # Policy section
    # ------------------------------------------------------------------ #
    def get_pcas_policy_section(self, policy_id: int, section_number: int) -> dict[str, Any]:
        """Get the details of one section within a compliance policy.

        Args:
            policy_id: ID of the policy that has the section.
            section_number: Section number to retrieve.

        Returns:
            JSON section document: sectionNumber, sectionHeading, and
            controls (each with technologies/evaluate/remediation).
        """
        params = {"policyId": policy_id, "sectionNumber": section_number}
        return self._gateway("/pcas/v3/policy/section", method="GET", params=params)

    def add_pcas_policy_section(self, policy_id: int, section_heading: str) -> dict[str, Any]:
        """Add a new section to a compliance policy.

        Remember to evaluate the policy after making changes.

        Args:
            policy_id: ID of the policy to add a section to.
            section_heading: Title for the new section.

        Returns:
            JSON ``{"sectionNumber", "sectionHeading", "controls": []}`` for
            the newly created section.
        """
        body = {"policyId": policy_id, "sectionHeading": section_heading}
        return self._gateway("/pcas/v3/policy/section", method="POST", json=body)

    def update_pcas_policy_section(self, policy_id: int, section_number: int, section_heading: str) -> dict[str, Any]:
        """Rename an existing section within a compliance policy.

        Remember to evaluate the policy after making changes.

        Args:
            policy_id: ID of the policy that has the section.
            section_number: Section number to update.
            section_heading: New title for the section.

        Returns:
            Empty dict on success (HTTP 204 has no body), or an error dict.
        """
        body = {
            "policyId": policy_id,
            "sectionNumber": section_number,
            "sectionHeading": section_heading,
        }
        return self._gateway("/pcas/v3/policy/section", method="PUT", json=body)

    def delete_pcas_policy_section(self, policy_id: int, section_number: int) -> dict[str, Any]:
        """Delete a section (and its controls' section membership) from a compliance policy.

        Remember to evaluate the policy after making changes.

        Args:
            policy_id: ID of the policy that has the section.
            section_number: Section number to delete.

        Returns:
            Empty dict on success (HTTP 204 has no body), or an error dict.
        """
        params = {"policyId": policy_id, "sectionNumber": section_number}
        return self._gateway("/pcas/v3/policy/section", method="DELETE", params=params)

    # ------------------------------------------------------------------ #
    # Policy section control
    # ------------------------------------------------------------------ #
    def get_pcas_policy_section_control(self, policy_id: int, section_number: int, control_id: int) -> dict[str, Any]:
        """Get one control's details within a specific policy section.

        Args:
            policy_id: ID of the policy that has the section.
            section_number: Section number that has the control.
            control_id: ID of the control to retrieve.

        Returns:
            JSON control document: controlId, sectionNumber, controlNumber,
            statement, criticality, isControlDisable, technologies
            (evaluate/remediation/rationale per technology).
        """
        params = {"policyId": policy_id, "sectionNumber": section_number, "controlId": control_id}
        return self._gateway("/pcas/v3/policy/section/control", method="GET", params=params)

    def add_pcas_policy_section_control(
        self,
        policy_id: int,
        section_number: int,
        control_id: int,
        reference_text: str | None = None,
        criticality: str | None = None,
        is_control_disable: bool | None = None,
        control_number: int | None = None,
    ) -> dict[str, Any]:
        """Add one control to a section within a compliance policy.

        Remember to evaluate the policy after making changes.

        Args:
            policy_id: ID of the policy to add the control to.
            section_number: Section number to add the control into.
            control_id: ID of the control to add.
            reference_text: Reference text for the control. Defaults to the
                control's own reference text when not provided.
            criticality: Criticality label for the control. Defaults to the
                control's own default criticality when not provided. One of:
                CRITICAL, MEDIUM, UNDEFINED, URGENT, MINIMAL, SERIOUS.
            is_control_disable: True to add the control disabled; defaults to
                enabled when not provided.
            control_number: Position within the section to insert the
                control at; defaults to the end of the section.

        Returns:
            JSON list containing the newly added control's full document.
        """
        control: dict[str, Any] = {"controlId": control_id}
        if reference_text is not None:
            control["referenceText"] = reference_text
        if criticality is not None:
            control["criticality"] = criticality
        if is_control_disable is not None:
            control["isControlDisable"] = is_control_disable
        if control_number is not None:
            control["controlNumber"] = control_number
        body = {
            "policyId": policy_id,
            "sectionNumber": section_number,
            "controls": [control],
        }
        return self._gateway("/pcas/v3/policy/section/control", method="POST", json=body)

    def update_pcas_policy_section_control(
        self,
        policy_id: int,
        section_number: int,
        control_id: int,
        criticality: str | None = None,
        reference_text: str | None = None,
        is_control_disable: bool | None = None,
        control_number: int | None = None,
    ) -> dict[str, Any]:
        """Update a control within a section of a compliance policy.

        Remember to evaluate the policy after making changes.

        Args:
            policy_id: ID of the policy that has the control.
            section_number: Section number that has the control.
            control_id: ID of the control to update.
            criticality: New criticality label. One of: CRITICAL, MEDIUM,
                UNDEFINED, URGENT, MINIMAL, SERIOUS.
            reference_text: New reference text for the control.
            is_control_disable: True to disable the control, False to enable
                it.
            control_number: New position for the control within the section.

        Returns:
            Empty dict on success (HTTP 204 has no body), or an error dict.
        """
        body: dict[str, Any] = {
            "policyId": policy_id,
            "sectionNumber": section_number,
            "controlId": control_id,
        }
        if criticality is not None:
            body["criticality"] = criticality
        if reference_text is not None:
            body["referenceText"] = reference_text
        if is_control_disable is not None:
            body["isControlDisable"] = is_control_disable
        if control_number is not None:
            body["controlNumber"] = control_number
        return self._gateway("/pcas/v3/policy/section/control", method="PUT", json=body)

    def delete_pcas_policy_section_control(self, policy_id: int, section_number: int, control_id: int) -> dict[str, Any]:
        """Remove a control from a section within a compliance policy.

        Remember to evaluate the policy after making changes.

        Args:
            policy_id: ID of the policy that has the control.
            section_number: Section number that has the control.
            control_id: ID of the control to remove.

        Returns:
            Empty dict on success (HTTP 204 has no body), or an error dict.
        """
        params = {"policyId": policy_id, "sectionNumber": section_number, "controlId": control_id}
        return self._gateway("/pcas/v3/policy/section/control", method="DELETE", params=params)

    # ------------------------------------------------------------------ #
    # Policy section control technology
    # ------------------------------------------------------------------ #
    def list_pcas_control_technologies(self, policy_id: int, section_number: int, control_id: int) -> dict[str, Any]:
        """List technologies associated with a control within a policy section.

        Args:
            policy_id: ID of the policy that has the control.
            section_number: Section number that has the control.
            control_id: ID of the control to list technologies for.

        Returns:
            JSON ``{"policyId", "sectionNumber", "controlId", "technologies":
            [...]}`` with evaluate/remediation/rationale per technology.
        """
        params = {"policyId": policy_id, "sectionNumber": section_number, "controlId": control_id}
        return self._gateway("/pcas/v3/policy/section/control/technology", method="GET", params=params)

    def add_pcas_control_technologies(
        self, policy_id: int, section_number: int, control_id: int, technology_ids: str
    ) -> dict[str, Any]:
        """Add technologies to a control within a policy section.

        Remember to evaluate the policy after making changes.

        Args:
            policy_id: ID of the policy that has the control.
            section_number: Section number that has the control.
            control_id: ID of the control to add technologies to.
            technology_ids: Comma-separated technology IDs to add.

        Returns:
            JSON list of the control's technologies after the add.
        """
        body = {
            "policyId": policy_id,
            "sectionNumber": section_number,
            "controlId": control_id,
            "technologyIds": [int(t) for t in technology_ids.split(",") if t.strip()],
        }
        return self._gateway("/pcas/v3/policy/section/control/technology", method="POST", json=body)

    def remove_pcas_control_technology(
        self, policy_id: int, section_number: int, control_id: int, technology_id: int
    ) -> dict[str, Any]:
        """Remove one technology from a control within a policy section.

        Remember to evaluate the policy after making changes.

        Args:
            policy_id: ID of the policy that has the control.
            section_number: Section number that has the control.
            control_id: ID of the control to remove the technology from.
            technology_id: ID of the technology to remove.

        Returns:
            Empty dict on success (HTTP 204 has no body), or an error dict.
        """
        params = {
            "policyId": policy_id,
            "sectionNumber": section_number,
            "controlId": control_id,
            "technologyId": technology_id,
        }
        return self._gateway("/pcas/v3/policy/section/control/technology", method="DELETE", params=params)

    # ------------------------------------------------------------------ #
    # Policy section control technology evaluate
    # ------------------------------------------------------------------ #
    def get_pcas_control_technology_evaluation(
        self, policy_id: int, section_number: int, control_id: int, technology_id: int
    ) -> dict[str, Any]:
        """Get the evaluation fields for one technology on a control within a policy section.

        Args:
            policy_id: ID of the policy that has the control.
            section_number: Section number that has the control.
            control_id: ID of the control.
            technology_id: ID of the technology to get evaluation fields for.

        Returns:
            JSON control document including the technology's ``evaluate``
            block (dp, op, v, fv) and remediation/rationale.
        """
        params = {
            "policyId": policy_id,
            "sectionNumber": section_number,
            "controlId": control_id,
            "technologyId": technology_id,
        }
        return self._gateway("/pcas/v3/policy/section/control/technology/evaluation", method="GET", params=params)

    def update_pcas_control_technology_evaluation(
        self,
        policy_id: int,
        section_number: int,
        control_id: int,
        technology_id: int,
        evaluate: dict[str, Any],
        remediation: str | None = None,
    ) -> dict[str, Any]:
        """Update evaluation fields for one technology on a control within a policy section.

        Remember to evaluate the policy after making changes.

        Args:
            policy_id: ID of the policy that has the control.
            section_number: Section number that has the control.
            control_id: ID of the control.
            technology_id: ID of the technology to update evaluation fields
                for.
            evaluate: Evaluation data-point payload, e.g.
                ``{"dp": {"k": "<key>", "v": ["<value>"], "op": "eq",
                "cd": "is contained in", "fv": [{"value": "...",
                "set": "1", "description": "..."}]}}``. Supported operators
                (op): eq, lt, le, gt, ge, ne, xeq, xre, re, range, in.
                Supported cardinalities (cd, for xeq/xre/re): match none,
                match all, match any, empty, not empty, contain, does not
                contain, match, intersect, is contained in.
            remediation: New remediation text for this technology/control.

        Returns:
            Empty dict on success (HTTP 204 has no body), or an error dict.
        """
        body: dict[str, Any] = {
            "policyId": policy_id,
            "sectionNumber": section_number,
            "controlId": control_id,
            "technologyId": technology_id,
            "evaluate": evaluate,
        }
        if remediation is not None:
            body["remediation"] = remediation
        return self._gateway("/pcas/v3/policy/section/control/technology/evaluation", method="PUT", json=body)

    # ------------------------------------------------------------------ #
    # Library
    # ------------------------------------------------------------------ #
    def list_pcas_library_labels(self) -> dict[str, Any]:
        """List all supported PCAS library labels (e.g. CIS, DISA STIG, Vendor, Mandate).

        Returns:
            JSON list of ``{"labelId", "labelName"}``.
        """
        return self._gateway("/pcas/v1/library/label", method="GET")

    def list_pcas_library_label_technologies(self, label_id: int | None = None) -> dict[str, Any]:
        """List technologies associated with a PCAS library label.

        Args:
            label_id: Label ID to restrict technologies to. Omit to return
                technologies for all labels.

        Returns:
            JSON ``{"technologies": [{"technologyId", "technologyName"}]}``.
        """
        return self._gateway("/pcas/v1/library/technology", method="GET", params={"labelId": label_id})

    def list_pcas_library_policies(
        self,
        label_id: int | None = None,
        technology_id: str | None = None,
        include_description: bool | None = None,
        updated_after: str | None = None,
    ) -> dict[str, Any]:
        """List library policies, optionally filtered by label and/or technology.

        Args:
            label_id: Restrict to policies associated with this label ID.
                Omit to return policies for all labels.
            technology_id: Comma-separated technology IDs to restrict to.
                Omit to return policies for all technologies.
            include_description: Include each policy's description text.
            updated_after: Only policies updated on/after this date. Format:
                dd/mm/yyyy.

        Returns:
            JSON list of ``{"policyId", "policyTitle"[, "description"],
            "version", "date"}``.
        """
        params = {
            "labelId": label_id,
            "technologyId": technology_id,
            "includeDescription": include_description,
            "updatedAfter": updated_after,
        }
        return self._gateway("/pcas/v1/library/policy/list", method="GET", params=params)

    def get_pcas_library_policy(
        self,
        policy_id: int | None = None,
        policy_title: str | None = None,
        details: str = "basic",
    ) -> dict[str, Any]:
        """Get details for a specific PCAS library policy.

        Provide exactly one of ``policy_id`` or ``policy_title``.

        Args:
            policy_id: ID of the library policy to fetch (from
                ``list_pcas_library_policies``).
            policy_title: Title of the library policy to fetch (URL-encode
                it yourself if it contains special characters, e.g. spaces
                as ``%20``).
            details: "basic" (default; minimal info) or "full" (complete
                details including sections and controls).

        Returns:
            JSON library policy document: policyId, policyTitle, coverPage,
            technologies, sections (with controls when details="full").
        """
        params = {"policyId": policy_id, "policyTitle": policy_title, "details": details}
        return self._gateway("/pcas/v1/library/policy", method="GET", params=params)

    def import_pcas_library_policy(
        self,
        policy_id: str,
        technology_ids: str | None = None,
        import_as_unlocked: bool | None = None,
        activate_policy: bool | None = None,
        policy_title: str | None = None,
    ) -> dict[str, Any]:
        """Import a PCAS library policy into the subscription as a new compliance policy.

        Args:
            policy_id: Library policy ID (from ``list_pcas_library_policies``
                or ``get_pcas_library_policy``) to import.
            technology_ids: Comma-separated technology IDs to import. Omit to
                import all technologies mapped to the policy.
            import_as_unlocked: True to import the policy unlocked, False
                (default behavior) to import it locked.
            activate_policy: True to import the policy as active, False to
                import it inactive.
            policy_title: Title for the newly imported policy.

        Returns:
            JSON ``{"message", "policyId", "imported", "active"}``.
        """
        body: dict[str, Any] = {"policyId": policy_id}
        if technology_ids is not None:
            body["technologyIds"] = [t.strip() for t in technology_ids.split(",") if t.strip()]
        if import_as_unlocked is not None:
            body["importAsUnlocked"] = import_as_unlocked
        if activate_policy is not None:
            body["activatePolicy"] = activate_policy
        if policy_title is not None:
            body["policyTitle"] = policy_title
        return self._gateway("/pcas/v1/library/policy/import", method="POST", json=body)
