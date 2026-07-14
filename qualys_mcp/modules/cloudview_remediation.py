"""TotalCloud / CloudView — Remediation module (Gateway/JWT REST API).

CSPM remediation surface: list and inspect remediation activities, trigger
one-click remediation of a failing resource/control, and enable/disable
remediation rules.

All endpoints are on the Gateway host under ``/cloudview-api/rest/v1/...`` and
use JWT bearer auth (auto-fetched by ``self._gateway``). Remediation is only
available to Cloud Security Assessment (CSA)/TotalCloud remediation
subscribers.

Docs: Qualys TotalCloud / CloudView — "Remediation" / "Remediation Activity".
https://docs.qualys.com/en/tc/api/

Note:
    # TODO(verify): The public CloudView/TotalCloud API docs do not clearly
    publish the remediation REST paths/bodies (remediation is largely
    documented as a UI feature under Responses > Remediation Activity, plus
    a ``remediationEnabled`` flag on connectors). Every path/body/param in
    this module is a best-effort reconstruction and MUST be verified against
    a live console or the current TotalCloud API notification before use.
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class CloudviewRemediationModule(BaseModule):
    """List, inspect, and trigger TotalCloud/CloudView remediation, and manage rules."""

    module_label = "cloudview_remediation"

    def register_tools(self, server: FastMCP) -> None:
        self._add_tool(server, self.list_remediation_activities, "list_remediation_activities", tier="read")
        self._add_tool(server, self.get_remediation_activity, "get_remediation_activity", tier="read")
        self._add_tool(server, self.trigger_remediation, "trigger_remediation", tier="write")
        self._add_tool(server, self.set_remediation_rule, "set_remediation_rule", tier="write")

    # ------------------------------------------------------------------ #
    # Reads
    # ------------------------------------------------------------------ #
    def list_remediation_activities(
        self,
        cloud_provider: str | None = None,
        page_no: int | None = None,
        page_size: int | None = None,
        filter: str | None = None,
    ) -> dict[str, Any]:
        """List remediation activities across cloud providers.

        Path/params confirmed via the qualysdk open-source client's
        TotalCloud call schema (independent reconstruction of the real
        endpoint, since Qualys's public docs don't clearly publish this
        path): ``GET /cloudview-api/rest/v1/remediation/activity``
        (singular ``activity``, not ``activities`` — the previous guess
        404'd in the live audit), with query params ``pageNo``, ``pageSize``,
        ``filter``, and ``cloudType``.

        Args:
            cloud_provider: One of "aws", "azure", "gcp" — sent as the
                ``cloudType`` query param. Omit to list across all providers.
            page_no: Page number to return (0-based).
            page_size: Number of records per page.
            filter: QQL filter string (e.g. by connector, control, status,
                or date).

        Returns:
            JSON remediation activity list, or an error dict.
        """
        params = {
            "pageNo": page_no,
            "pageSize": page_size,
            "filter": filter,
            "cloudType": cloud_provider.upper() if cloud_provider else None,
        }
        return self._gateway("/cloudview-api/rest/v1/remediation/activity", method="GET", params=params)

    def get_remediation_activity(self, activity_id: str) -> dict[str, Any]:
        """Get details for a single remediation activity.

        Args:
            activity_id: The remediation activity ID to fetch.

        Returns:
            JSON remediation activity detail, or an error dict.

        Note:
            # TODO(verify): the collection path is confirmed as
            ``/cloudview-api/rest/v1/remediation/activity`` (see
            :meth:`list_remediation_activities`); this assumes the
            conventional ``/{activityId}`` suffix for a single record, which
            is not independently confirmed — verify against a live console.
        """
        return self._gateway(
            f"/cloudview-api/rest/v1/remediation/activity/{activity_id}", method="GET"
        )

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #
    def trigger_remediation(
        self,
        cloud_provider: str,
        connector_id: str,
        control_id: str,
        resource_id: str,
        account_id: str | None = None,
        additional_fields: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Trigger one-click remediation for a failing resource/control.

        Args:
            cloud_provider: One of "aws", "azure", "gcp".
            connector_id: The connector ID (UUID) owning the resource.
            control_id: The control ID (CID) whose failure to remediate.
            resource_id: The resource ID to remediate.
            account_id: Optional cloud account/subscription/project ID the
                resource belongs to.
            additional_fields: Escape hatch for any documented body fields
                not exposed above (merged into the request body verbatim,
                e.g. remediation action parameters).

        Returns:
            JSON trigger result (typically a remediation activity/job
            reference), or an error dict.

        Note:
            # TODO(verify): Path and body are best-effort. Path guessed as
            ``POST /cloudview-api/rest/v1/remediation`` with body keys
            cloudType/connectorId/controlId/resourceId/accountId. Confirm the
            real endpoint (it may be provider-scoped like
            ``/{provider}/remediation`` or require a remediation-rule/action
            ID) and body schema.
        """
        provider = cloud_provider.lower().strip()
        if provider not in ("aws", "azure", "gcp"):
            return {"error": "cloud_provider must be one of: aws, azure, gcp"}
        body: dict[str, Any] = {
            "cloudType": provider.upper(),
            "connectorId": connector_id,
            "controlId": control_id,
            "resourceId": resource_id,
        }
        if account_id is not None:
            body["accountId"] = account_id
        if additional_fields:
            body.update(additional_fields)
        return self._gateway("/cloudview-api/rest/v1/remediation", method="POST", json=body)

    def set_remediation_rule(
        self,
        rule_id: str,
        enabled: bool,
    ) -> dict[str, Any]:
        """Enable or disable a remediation rule.

        Args:
            rule_id: The remediation rule ID to update.
            enabled: True to enable the rule, False to disable it.

        Returns:
            JSON update result (often empty on success), or an error dict.

        Note:
            # TODO(verify): Path and method are best-effort. Guessed as
            ``PATCH /cloudview-api/rest/v1/remediation/rules/{ruleId}`` with
            body ``{"enabled": <bool>}``. Confirm the real path (rules may
            live under ``/remediation/rule`` or an automation/QFlow
            sub-resource), the method (PATCH vs PUT vs POST), and the body /
            enable-disable action shape.
        """
        body = {"enabled": enabled}
        return self._gateway(
            f"/cloudview-api/rest/v1/remediation/rules/{rule_id}", method="PATCH", json=body
        )
