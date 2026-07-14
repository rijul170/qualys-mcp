"""Policy Compliance — Compliance Framework Reports module (Gateway/JWT REST API).

Covers the mandate/framework-based compliance reporting APIs used to build,
poll, and download "Compliance Framework Reports" (e.g. PCI DSS, HIPAA)
across one or more policies, scoped by all assets in the policy, asset
groups, or asset tags.

Docs: Qualys VM/PC API User Guide — "Compliance Framework Reports" (GET
Preferred Framework List, GET Policies List, GET Asset Groups List, GET Asset
Tags List, GET Asset Sources List, Create Compliance Framework Report, GET
Report Generation Status, Download Compliance Framework Report).
Endpoints: ``/pcrs/1.0/mandate/...``.
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class ComplianceFrameworkReportsModule(BaseModule):
    """Build and retrieve mandate/framework-based Policy Compliance (PC) reports."""

    module_label = "compliance_framework_reports"

    def register_tools(self, server: FastMCP) -> None:
        self._add_tool(server, self.list_preferred_frameworks, "list_preferred_frameworks", tier="read")
        self._add_tool(server, self.list_framework_policies, "list_framework_policies", tier="read")
        self._add_tool(server, self.list_framework_asset_groups, "list_framework_asset_groups", tier="read")
        self._add_tool(server, self.list_framework_asset_tags, "list_framework_asset_tags", tier="read")
        self._add_tool(server, self.list_framework_report_sources, "list_framework_report_sources", tier="read")
        self._add_tool(server, self.create_framework_report, "create_framework_report", tier="write")
        self._add_tool(server, self.get_framework_report_status, "get_framework_report_status", tier="read")
        self._add_tool(server, self.download_framework_report, "download_framework_report", tier="read")

    def list_preferred_frameworks(self) -> dict[str, Any]:
        """List preferred compliance frameworks (mandates) configured for the subscription.

        Returns:
            JSON list of ``{"id", "name", "requirementsCount"}`` (top-level
            requirement count per mandate, e.g. "PCI DSS v4.0", "HIPAA").
        """
        return self._gateway("/pcrs/1.0/mandate/list", method="GET")

    def list_framework_policies(self) -> dict[str, Any]:
        """List all active compliance policies available for framework reports.

        Returns:
            JSON list of ``{"id", "title"}``.
        """
        return self._gateway("/pcrs/1.0/policy/list", method="GET")

    def list_framework_asset_groups(self) -> dict[str, Any]:
        """List asset groups available for scoping a framework report.

        Requires Asset Group Management System (AGMS) to be enabled for the
        subscription.

        Returns:
            JSON list of ``{"id", "name"}``.
        """
        return self._gateway("/pcrs/1.0/assetGroup/list", method="GET")

    def list_framework_asset_tags(self) -> dict[str, Any]:
        """List the hierarchical asset tag tree available for scoping a framework report.

        Returns:
            JSON list of ``{"id", "name", "isFavorite", "children": [...]}``
            (nested recursively).
        """
        return self._gateway("/pcrs/1.0/assetTag/list", method="GET")

    def list_framework_report_sources(self) -> dict[str, Any]:
        """List the available asset source options for creating a framework report.

        Returns:
            JSON list of source names, e.g. ["All Assets In Policy", "Asset
            Groups", "Asset Tags"].
        """
        return self._gateway("/pcrs/1.0/mandate/report/sources", method="GET")

    def create_framework_report(
        self,
        title: str,
        mandate_ids: str,
        policy_ids: str,
        selection_type: str = "All Assets In Policy",
        report_format: str = "JSON",
        asset_group_ids: str | None = None,
        include_tag_ids: str | None = None,
        exclude_tag_ids: str | None = None,
        include_tag_resolution: str = "Any",
        exclude_tag_resolution: str = "Any",
        schedule_type: str = "ONDEMAND",
    ) -> dict[str, Any]:
        """Create (generate) a new compliance framework report.

        Maximum 3 mandate IDs and 10 policies may be selected per report.

        Args:
            title: Title for the report.
            mandate_ids: Comma-separated mandate/framework IDs (max 3; from
                ``list_preferred_frameworks``).
            policy_ids: Comma-separated policy IDs (max 10; from
                ``list_framework_policies``).
            selection_type: Asset source type (from
                ``list_framework_report_sources``) — "All Assets In Policy"
                (default), "Asset Groups", or "Asset Tags".
            report_format: "JSON" (default) or "HTML".
            asset_group_ids: Comma-separated asset group IDs. Required when
                ``selection_type`` is "Asset Groups".
            include_tag_ids: Comma-separated tag IDs to include. Used when
                ``selection_type`` is "Asset Tags".
            exclude_tag_ids: Comma-separated tag IDs to exclude. Used when
                ``selection_type`` is "Asset Tags".
            include_tag_resolution: "Any" (default) or "All" — how included
                tags are matched. Only used with tag filters.
            exclude_tag_resolution: "Any" (default) or "All" — how excluded
                tags are matched. Only used with tag filters.
            schedule_type: Report schedule type — "ONDEMAND" (default) runs
                the report immediately.

        Returns:
            JSON ``{"reportId", "message"}`` — use ``reportId`` as
            ``report_data_id`` with ``get_framework_report_status`` and
            ``download_framework_report``.
        """
        filters: dict[str, Any] = {
            "mandateIds": [int(m) for m in mandate_ids.split(",") if m.strip()],
            "policyIds": [int(p) for p in policy_ids.split(",") if p.strip()],
        }
        if asset_group_ids is not None:
            filters["assetGroupIds"] = [int(a) for a in asset_group_ids.split(",") if a.strip()]
        if include_tag_ids is not None or exclude_tag_ids is not None:
            filters["tagsetInputParam"] = {
                "includeTagResolution": include_tag_resolution,
                "excludeTagResolution": exclude_tag_resolution,
                "includeTagIds": [int(t) for t in include_tag_ids.split(",") if t.strip()]
                if include_tag_ids
                else [],
                "excludeTagIds": [int(t) for t in exclude_tag_ids.split(",") if t.strip()]
                if exclude_tag_ids
                else [],
            }
        body = {
            "title": title,
            "reportFormat": report_format,
            "selectionType": selection_type,
            "filters": filters,
            "schedule": {"scheduleType": schedule_type},
        }
        return self._gateway("/pcrs/1.0/mandate/report", method="POST", json=body)

    def get_framework_report_status(self, report_data_id: str) -> dict[str, Any]:
        """Get the generation status of a compliance framework report.

        Args:
            report_data_id: Report data ID returned by
                ``create_framework_report`` (as ``reportId``).

        Returns:
            JSON ``{"status", "percentageCompleted"}``.
        """
        return self._gateway(
            "/pcrs/1.0/mandate/report/status", method="GET", params={"reportDataId": report_data_id}
        )

    def download_framework_report(self, report_data_id: str) -> dict[str, Any]:
        """Download a completed compliance framework report (HTML format, zipped).

        Args:
            report_data_id: Report data ID returned by
                ``create_framework_report`` (as ``reportId``).

        Returns:
            The response body from the shared gateway wrapper.

        Note:
            # TODO(verify): This endpoint returns a binary zip file
            (containing the HTML report), not JSON. The shared
            ``self._gateway()`` wrapper parses responses as JSON and falls
            back to ``{"raw": resp.text}`` on non-JSON bodies, which can
            mangle binary content. Confirm actual behavior against a live
            console; a shared binary-download helper may be needed for
            reliable use.
        """
        return self._gateway(
            "/pcrs/1.0/mandate/report/download/html", method="GET", params={"reportDataId": report_data_id}
        )
