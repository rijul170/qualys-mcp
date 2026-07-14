"""Policy Compliance — Posture Information module (classic FO + PCRS gateway).

Covers both posture data retrieval paths described in the VM/PC User Guide:

* Classic "PC Posture Information" API (``/api/2.0/fo/compliance/posture/info/``)
  — recommended when the total posture data is under ~1 million records.
* "PC Posture Streaming" APIs (``/pcrs/<version>/posture/...`` on the Gateway,
  JWT bearer auth) — recommended for larger volumes; used in sequence:
  get policy list -> resolve host IDs -> get posture info (streamed JSON).

Docs: Qualys VM/PC API User Guide — "Compliance Posture Information", "PC
Posture Streaming APIs".
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class PcPostureModule(BaseModule):
    """Retrieve Policy Compliance (PC) posture information."""

    module_label = "pc_posture"

    def register_tools(self, server: FastMCP) -> None:
        self._add_tool(server, self.list_posture_policies, "list_posture_policies", tier="read")
        self._add_tool(server, self.resolve_posture_host_ids, "resolve_posture_host_ids", tier="read")
        self._add_tool(server, self.list_posture_info, "list_posture_info", tier="read")
        self._add_tool(server, self.stream_posture_info, "stream_posture_info", tier="read")

    # ------------------------------------------------------------------ #
    # PC Posture Streaming APIs (Gateway / JWT / /pcrs/...)
    # ------------------------------------------------------------------ #
    def list_posture_policies(
        self,
        last_evaluation_date: str | None = None,
        require_tag_info: bool | None = None,
        api_version: str = "2.0",
    ) -> dict[str, Any]:
        """List policy IDs for use with the PC Posture Streaming APIs.

        First step of the streaming sequence (get policy list -> resolve host
        IDs -> stream posture info). Optional — if you already have policy
        IDs, skip straight to ``resolve_posture_host_ids``.

        Args:
            last_evaluation_date: Only include policies with a posture
                evaluation on/after this date. Format: YYYY-MM-DD or
                YYYY-MM-DDTHH:MM:SSZ (UTC/GMT).
            require_tag_info: (v2.0 only) Include each policy's asset tag
                include/exclude configuration in the output.
            api_version: PCRS API version — "1.0" or "2.0" (default).

        Returns:
            JSON response with ``subscriptionId`` and ``policyList`` (each
            entry: id, title, createdBy/Date, modifiedBy/Date,
            lastEvaluatedDate, status, locked[, tagInfo]).

        Note:
            # TODO(verify): This module reaches PCRS (``/pcrs/...``) via
            ``self._gateway()`` (JWT Bearer on the configured gateway host).
            Doc samples show both ``https://gateway.<url>/...`` and
            ``<qualys_base_url>/...`` hosts for the same PCRS endpoints.
            Confirm the correct host for your platform.
        """
        params = {
            "lastEvaluationDate": last_evaluation_date,
            "requireTagInfo": require_tag_info,
        }
        return self._gateway(f"/pcrs/{api_version}/posture/policy/list", method="GET", params=params)

    def resolve_posture_host_ids(
        self,
        policy_id: str | None = None,
        last_scan_date: str | None = None,
        status_changed_since: str | None = None,
        asset_deployment_type: str | None = None,
        asset_state: str | None = None,
        api_version: str = "1.0",
    ) -> dict[str, Any]:
        """Resolve host IDs for one or more policies (streaming sequence step 2).

        Args:
            policy_id: Comma-separated policy ID(s) (max 10 for v1.0/v2.0).
                Required for api_version "1.0"/"2.0"; optional from "3.0"
                onward (omit to resolve hosts for all policies — Manager
                users only for v3.0+).
            last_scan_date: Only hosts last scanned on/after this date.
                Format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ.
            status_changed_since: (api_version "3.0"+) Only hosts with
                posture modified (failed or passed) on/after this date.
            asset_deployment_type: (api_version "5.0") Filter by deployment
                type — "ON-PREM", "CLOUD", or "ALL".
            asset_state: (api_version "5.0") Filter by asset state —
                "ACTIVE", "TERMINATED", or "ALL". Ignored when
                asset_deployment_type is "ON-PREM".
            api_version: PCRS API version — "1.0" (default), "2.0", "3.0",
                "4.0", or "5.0". Versions 3.0+ fetch PC asset data only (use
                "1.0"/"2.0" to also include SCA asset data).

        Returns:
            JSON list of ``{"policyId", "subscriptionId", "hostIds": [...]}``
            entries, one per requested policy.
        """
        params = {
            "policyId": policy_id,
            "lastScanDate": last_scan_date,
            "statusChangedSince": status_changed_since,
            "assetDeploymentType": asset_deployment_type,
            "assetState": asset_state,
        }
        return self._gateway(f"/pcrs/{api_version}/posture/hostids", method="GET", params=params)

    def stream_posture_info(
        self,
        policy_id: str,
        subscription_id: str,
        host_ids: str,
        evidence_required: bool | None = None,
        compression_required: bool | None = None,
        last_evaluation_date: str | None = None,
        last_scan_date: str | None = None,
        last_scan_date_from: str | None = None,
        last_scan_date_to: str | None = None,
        status_changed_since: str | None = None,
        exclude_inactive_control: bool | None = None,
        api_version: str = "2.0",
    ) -> dict[str, Any]:
        """Stream compliance posture info for resolved host IDs (streaming sequence step 3).

        Args:
            policy_id: Policy ID the host IDs were resolved against.
            subscription_id: Subscription ID returned by
                ``resolve_posture_host_ids``.
            host_ids: Comma-separated host IDs (from
                ``resolve_posture_host_ids``) to fetch posture for.
            evidence_required: Include evidence data (expected/current
                values) for each posture record. Increases response time.
            compression_required: Compress the response payload. Not
                compressing increases response time.
            last_evaluation_date: Only records evaluated on/after this date.
                Format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ.
            last_scan_date: Only records for assets last scanned on this
                date. Format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ.
            last_scan_date_from: Start of a last-scanned date range (must be
                paired with ``last_scan_date_to``; mutually exclusive with
                ``last_scan_date``).
            last_scan_date_to: End of a last-scanned date range.
            status_changed_since: Only records whose posture changed on/after
                this date. Format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ.
            exclude_inactive_control: Exclude posture for controls that have
                been removed/deactivated from the policy.
            api_version: PCRS API version — "1.0" or "2.0" (default; adds
                excludeInactiveControl and extended evidence/lastUpdated).

        Returns:
            JSON list of posture info records (control/host/technology IDs,
            status, dates, criticality, and evidence when requested).
        """
        params = {
            "evidenceRequired": evidence_required,
            "compressionRequired": compression_required,
            "lastEvaluationDate": last_evaluation_date,
            "lastScanDate": last_scan_date,
            "lastScanDateFrom": last_scan_date_from,
            "lastScanDateTo": last_scan_date_to,
            "statusChangedSince": status_changed_since,
            "excludeInactiveControl": exclude_inactive_control,
        }
        body = [
            {
                "policyId": policy_id,
                "subscriptionId": subscription_id,
                "hostIds": [h.strip() for h in host_ids.split(",") if h.strip()],
            }
        ]
        return self._gateway(f"/pcrs/{api_version}/posture/postureInfo", method="POST", params=params, json=body)

    # ------------------------------------------------------------------ #
    # Classic PC Posture Information API (FO)
    # ------------------------------------------------------------------ #
    def list_posture_info(
        self,
        policy_id: str | None = None,
        policy_ids: str | None = None,
        output_format: str = "xml",
        details: str = "Basic",
        hide_evidence: bool | None = None,
        show_extended_evidence: bool | None = None,
        include_dp_name: bool | None = None,
        show_remediation_info: bool | None = None,
        truncation_limit: int | None = None,
        ips: str | None = None,
        host_ids: str | None = None,
        control_ids: str | None = None,
        status: str | None = None,
        status_changes_since: str | None = None,
        evaluation_date: str | None = None,
        asset_group_ids: str | None = None,
        criticality_labels: str | None = None,
        criticality_values: str | None = None,
        echo_request: bool | None = None,
    ) -> dict[str, Any]:
        """List compliance posture info records for one or more policies (non-streaming).

        Recommended when total posture data is under ~1 million records; use
        the streaming APIs (``list_posture_policies`` /
        ``resolve_posture_host_ids`` / ``stream_posture_info``) above that.

        Args:
            policy_id: Single policy ID (mutually exclusive with
                ``policy_ids``; required for csv output_format).
            policy_ids: Comma-separated policy IDs, up to 10 (mutually
                exclusive with ``policy_id``; downloads all data, and
                ``truncation_limit`` is invalid when set).
            output_format: "xml" (default), "csv" (posture + metadata), or
                "csv_no_metadata" (posture data only). CSV requires
                ``policy_id`` (not ``policy_ids``).
            details: "None" (posture + minimal exception info), "Basic"
                (default; adds full exception info + minimal glossary),
                "Light" (adds limited glossary + evidence), or "All" (adds
                pass percentage, summary, and full glossary).
            hide_evidence: Hide evidence info when details is "All"/"Light".
            show_extended_evidence: Show extended evidence info when details
                is "All"/"Light" (mutually exclusive with hide_evidence=True).
            include_dp_name: Include the name and ID for each data point.
            show_remediation_info: Include remediation information.
            truncation_limit: Max posture records per page (default 5000;
                only valid with ``policy_id``; 0 = no limit).
            ips: Comma-separated IPs/ranges to restrict hosts to.
            host_ids: Comma-separated host IDs and/or ID ranges.
            control_ids: Comma-separated control IDs and/or ID ranges.
            status: "Passed", "Failed", or "Error" (default: all statuses).
            status_changes_since: ISO date/time — only records whose status
                changed on/after this date.
            evaluation_date: ISO date/time — only records evaluated on/after
                this date.
            asset_group_ids: Comma-separated asset group IDs to restrict
                hosts to (need not be assigned to the requested policy).
            criticality_labels: Comma-separated criticality labels (e.g.
                SERIOUS, CRITICAL, URGENT). Mutually exclusive with
                ``criticality_values``.
            criticality_values: Comma-separated criticality values (0-5).
                Mutually exclusive with ``criticality_labels``.
            echo_request: Echo the request's input parameters in the output.

        Returns:
            Parsed POSTURE_INFO_LIST_OUTPUT (or ``{"raw": ...}`` for CSV
            output formats).
        """
        params = {
            "action": "list",
            "policy_id": policy_id,
            "policy_ids": policy_ids,
            "output_format": output_format,
            "details": details,
            "hide_evidence": hide_evidence,
            "show_extended_evidence": show_extended_evidence,
            "include_dp_name": include_dp_name,
            "show_remediation_info": show_remediation_info,
            "truncation_limit": truncation_limit,
            "ips": ips,
            "host_ids": host_ids,
            "control_ids": control_ids,
            "status": status,
            "status_changes_since": status_changes_since,
            "evaluation_date": evaluation_date,
            "asset_group_ids": asset_group_ids,
            "criticality_labels": criticality_labels,
            "criticality_values": criticality_values,
            "echo_request": echo_request,
        }
        parse = output_format == "xml"
        return self._fo("/api/2.0/fo/compliance/posture/info/", method="GET", params=params, parse=parse)
