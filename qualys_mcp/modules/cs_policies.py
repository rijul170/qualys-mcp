"""Container Security — Policies module (Gateway/JWT API).

Container Security is a Gateway-family product: calls go to the gateway host
(JWT auto-fetched) under ``/csapi/v1.3/...`` with JSON bodies — no ``/qps/rest``
prefix and no XML. Not in the VM/PC PDF; endpoint shapes come from the public
CS API reference (https://docs.qualys.com/en/cs/api/ and CS API release notes).
Uncertain paths/params/bodies are flagged with ``# TODO(verify)``.

The CS "centralized policy" surface covers admission-controller / CI-CD policies
(the confirmed create/update endpoints are ``centralizedPolicy``). List/get/
delete forms are inferred by REST convention and marked accordingly.

Docs: Qualys Container Security API Guide — "Policy".
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class CsPoliciesModule(BaseModule):
    """List, inspect, and manage Container Security (centralized) policies."""

    module_label = "cs_policies"

    # Base path for the centralized-policy resource.
    _BASE = "/csapi/v1.3/centralizedPolicy"  # TODO(verify): confirm this is the
    # correct resource for list/get/delete (create/update are confirmed here).

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(server, self.list_cs_policies, "list_cs_policies", tier="read")
        self._add_tool(server, self.get_cs_policy, "get_cs_policy", tier="read")
        # Writes
        self._add_tool(server, self.create_cs_policy, "create_cs_policy", tier="write")
        self._add_tool(server, self.update_cs_policy, "update_cs_policy", tier="write")
        # Destructive
        self._add_tool(server, self.delete_cs_policy, "delete_cs_policy", tier="destructive")

    # ------------------------------------------------------------------ #
    # Reads
    # ------------------------------------------------------------------ #
    def list_cs_policies(
        self,
        filter: str | None = None,
        page_number: int | None = None,
        page_size: int = 50,
        sort: str | None = None,
    ) -> dict[str, Any]:
        """List container security policies (and their assessment status).

        Args:
            filter: Qualys QQL-style filter string (``filter`` query param).
            page_number: Zero-based page index (``pageNumber`` query param).
            page_size: Results per page (``pageSize`` query param; default 50).
            sort: Sort expression (``sort`` query param).

        Returns:
            Parsed JSON with a ``data`` array of policy records.
        """
        params = {
            "filter": filter,
            "pageNumber": page_number,
            "pageSize": page_size,
            "sort": sort,
        }
        # TODO(verify): list path/method — assumed GET on the centralizedPolicy
        # resource; the CS "assessment" listing may live at a different path.
        return self._gateway(self._BASE, method="GET", params=params)

    def get_cs_policy(self, policy_id: str) -> dict[str, Any]:
        """Fetch details of a single policy.

        Args:
            policy_id: The policy ID (``policyId``).

        Returns:
            Parsed JSON policy record (rules, scope, actions).
        """
        # TODO(verify): get-by-id path — assumed GET {base}/{policyId}.
        return self._gateway(f"{self._BASE}/{policy_id}", method="GET")

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #
    def create_cs_policy(
        self,
        name: str,
        policy_type: str,
        description: str | None = None,
        enabled: bool = True,
        action: str | None = None,
    ) -> dict[str, Any]:
        """Create a new centralized policy (admission-controller or CI-CD).

        Args:
            name: Policy name (``name``).
            policy_type: Policy type — e.g. "ADMISSION_CONTROLLER" or "CICD".
                # TODO(verify): exact ``policyType``/``type`` field name and enum.
            description: Optional description.
            enabled: Whether the policy is active on creation.
            action: Enforcement action on match — e.g. "BLOCK", "ALERT",
                "AUDIT". # TODO(verify): field name and enum values.

        Returns:
            Parsed JSON with the created policy's ID, or an error dict.

        Note:
            This tool exposes only top-level policy fields. The full policy body
            includes nested authorization/vulnerability rule arrays whose exact
            schema is version-specific.
            # TODO(verify): nested ``rules``/``authorizationRules``/
            # ``vulnerabilityRules`` structure — not modeled here; callers needing
            # rich rules must extend this body.
        """
        body: dict[str, Any] = {
            "name": name,
            "policyType": policy_type,  # TODO(verify): field name
            "enabled": enabled,
        }
        if description is not None:
            body["description"] = description
        if action is not None:
            body["action"] = action  # TODO(verify): field name
        # Confirmed: POST /csapi/v1.3/centralizedPolicy
        return self._gateway(self._BASE, method="POST", json=body)

    def update_cs_policy(
        self,
        policy_id: str,
        name: str | None = None,
        description: str | None = None,
        enabled: bool | None = None,
        action: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing centralized policy.

        Args:
            policy_id: The policy ID to update (``policyId``).
            name: New policy name, if changing.
            description: New description, if changing.
            enabled: Enable/disable the policy, if changing.
            action: New enforcement action, if changing. # TODO(verify): enum.

        Returns:
            Parsed JSON with the updated policy record, or an error dict.
        """
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        if enabled is not None:
            body["enabled"] = enabled
        if action is not None:
            body["action"] = action  # TODO(verify): field name
        # Confirmed: PUT /csapi/v1.3/centralizedPolicy/{policyId}
        return self._gateway(f"{self._BASE}/{policy_id}", method="PUT", json=body)

    # ------------------------------------------------------------------ #
    # Destructive
    # ------------------------------------------------------------------ #
    def delete_cs_policy(self, policy_id: str, confirm: str | None = None) -> dict[str, Any]:
        """Permanently delete a policy. IRREVERSIBLE.

        Gated: requires the console to be started with QUALYS_ENABLE_DESTRUCTIVE
        and the caller to pass confirm=<policy_id>.

        Args:
            policy_id: The policy ID to delete.
            confirm: Must equal ``policy_id`` to proceed.

        Returns:
            Parsed JSON status, or a confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=policy_id)
        if guard:
            return guard
        # TODO(verify): delete path/method — assumed
        # DELETE /csapi/v1.3/centralizedPolicy/{policyId}.
        return self._gateway(f"{self._BASE}/{policy_id}", method="DELETE")
