"""Policy Compliance — Compliance Controls module (classic FO + PCAS gateway).

Covers the Compliance Control List (classic FO,
``/api/2.0/fo/compliance/control/``) and Control Criticality get/set. Control
Criticality itself has no dedicated subscription-wide API documented in the
VM/PC User Guide (see the per-tool notes below); the closest documented get
path is the standard control list (which returns each control's CRITICALITY
block), and the closest documented set path is the PCAS Policy Section
Control API, which overrides criticality per policy section.

Docs: Qualys VM/PC API User Guide — "Compliance Control List", "Control
Criticality".
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class PcControlsModule(BaseModule):
    """Query Policy Compliance (PC) controls and their criticality."""

    module_label = "pc_controls"

    def register_tools(self, server: FastMCP) -> None:
        self._add_tool(server, self.list_compliance_controls, "list_compliance_controls", tier="read")
        self._add_tool(server, self.get_control_criticality, "get_control_criticality", tier="read")
        self._add_tool(server, self.set_control_criticality, "set_control_criticality", tier="write")

    def list_compliance_controls(
        self,
        details: str = "Basic",
        ids: str | None = None,
        id_min: int | None = None,
        id_max: int | None = None,
        updated_after_datetime: str | None = None,
        created_after_datetime: str | None = None,
        truncation_limit: int | None = None,
        echo_request: bool | None = None,
    ) -> dict[str, Any]:
        """List compliance controls (System Defined Controls and UDCs) visible to the user.

        Args:
            details: Level of detail — "None" (control ID only), "Basic"
                (default: ID, category, sub-category, statement, technology
                info), or "All" (Basic plus framework mappings).
            ids: Comma-separated control IDs and/or ID ranges (e.g.
                "3000-3250").
            id_min: Lower bound control ID for a range query.
            id_max: Upper bound control ID for a range query.
            updated_after_datetime: ISO date/time (YYYY-MM-DD[THH:MM:SSZ]) —
                only controls updated after this.
            created_after_datetime: ISO date/time — only controls created
                after this.
            truncation_limit: Max control records per page (default 1000;
                0 = no limit — can generate very large output).
            echo_request: Echo the request's input parameters in the output.

        Returns:
            Parsed CONTROL_LIST_OUTPUT.
        """
        params = {
            "action": "list",
            "details": details,
            "ids": ids,
            "id_min": id_min,
            "id_max": id_max,
            "updated_after_datetime": updated_after_datetime,
            "created_after_datetime": created_after_datetime,
            "truncation_limit": truncation_limit,
            "echo_request": echo_request,
        }
        return self._fo("/api/2.0/fo/compliance/control/", method="GET", params=params)

    def get_control_criticality(self, ids: str) -> dict[str, Any]:
        """Get the criticality rating(s) for specific compliance controls.

        Control Criticality must be enabled for the subscription (contact
        Qualys Support or your TAM to enable it).

        Args:
            ids: Comma-separated control IDs (e.g. "1044,1045").

        Returns:
            Parsed CONTROL_LIST_OUTPUT; inspect each CONTROL's CRITICALITY
            (LABEL/VALUE) block.

        Note:
            # TODO(verify): The VM/PC User Guide's "Control Criticality"
            section only describes the feature and does not document a
            dedicated get-criticality endpoint. This reuses the standard
            control list endpoint (details=All) as the closest documented
            "get" path — confirm there isn't a more specific endpoint.
        """
        params = {"action": "list", "ids": ids, "details": "All"}
        return self._fo("/api/2.0/fo/compliance/control/", method="GET", params=params)

    def set_control_criticality(
        self,
        policy_id: int,
        section_number: int,
        control_id: int,
        criticality: str,
    ) -> dict[str, Any]:
        """Override a control's criticality within one policy section.

        Args:
            policy_id: ID of the policy containing the control.
            section_number: Section number within the policy that has the
                control.
            control_id: ID of the control to update.
            criticality: New criticality label. One of: CRITICAL, MEDIUM,
                UNDEFINED, URGENT, MINIMAL, SERIOUS.

        Returns:
            Empty dict on success (HTTP 204 has no body), or an error dict.

        Note:
            # TODO(verify): No subscription-wide/global control criticality
            setter is documented in the VM/PC User Guide; criticality can
            only be overridden per policy section via the PCAS Policy
            Section Control API (``PUT /pcas/v3/policy/section/control``)
            used here. Confirm this matches the intended "set" behavior for
            Control Criticality before relying on it.
        """
        body = {
            "policyId": policy_id,
            "sectionNumber": section_number,
            "controlId": control_id,
            "criticality": criticality,
        }
        return self._gateway("/pcas/v3/policy/section/control", method="PUT", json=body)
