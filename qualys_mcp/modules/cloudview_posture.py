"""TotalCloud / CloudView — Posture & Inventory module (Gateway/JWT REST API).

Read-focused CSPM posture surface: control metadata, per-account/per-control
evaluations (posture), evaluation stats, cloud resource inventory, and
policy/mandate lookups.

All endpoints are on the Gateway host under ``/cloudview-api/rest/v1/...`` and
use JWT bearer auth (auto-fetched by ``self._gateway``).

Docs: Qualys TotalCloud / CloudView API User Guide — "Controls",
"Evaluations", "Resource Inventory". https://docs.qualys.com/en/tc/api/
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule

_PROVIDERS = ("aws", "azure", "gcp")


class CloudviewPostureModule(BaseModule):
    """Query TotalCloud/CloudView controls, evaluations (posture), and resources."""

    module_label = "cloudview_posture"

    def register_tools(self, server: FastMCP) -> None:
        self._add_tool(server, self.list_controls, "list_cloudview_controls", tier="read")
        self._add_tool(server, self.get_control, "get_cloudview_control", tier="read")
        self._add_tool(server, self.list_evaluations, "list_cloudview_evaluations", tier="read")
        self._add_tool(server, self.list_control_evaluation_resources, "list_control_evaluation_resources", tier="read")
        self._add_tool(server, self.get_evaluation_stats, "get_cloudview_evaluation_stats", tier="read")
        self._add_tool(server, self.list_resources, "list_cloudview_resources", tier="read")
        self._add_tool(server, self.list_policies, "list_cloudview_policies", tier="read")

    @staticmethod
    def _norm_provider(cloud_provider: str) -> str | None:
        p = cloud_provider.lower().strip()
        return p if p in _PROVIDERS else None

    # ------------------------------------------------------------------ #
    # Controls
    # ------------------------------------------------------------------ #
    def list_controls(
        self,
        page_no: int | None = None,
        page_size: int | None = None,
        filter: str | None = None,
        sort: str | None = None,
    ) -> dict[str, Any]:
        """List CloudView control metadata (the CSPM control library).

        Args:
            page_no: Page number to return (0-based).
            page_size: Number of records per page.
            filter: QQL filter string (e.g.
                ``control.cloudType:AWS and control.criticality:HIGH``).
            sort: Sort expression, e.g. "cid:asc".

        Returns:
            JSON control metadata list envelope, or an error dict.
        """
        params = {"pageNo": page_no, "pageSize": page_size, "filter": filter, "sort": sort}
        return self._gateway("/cloudview-api/rest/v1/controls/metadata/list", method="GET", params=params)

    def get_control(self, control_id: str) -> dict[str, Any]:
        """Get metadata for a single CloudView control.

        Args:
            control_id: The control ID (CID) to fetch.

        Returns:
            JSON control metadata, or an error dict.

        Note:
            # TODO(verify): A dedicated single-control endpoint
            (``/cloudview-api/rest/v1/controls/metadata/{controlId}``) is not
            confirmed in the public docs — the documented path is the
            ``/controls/metadata/list`` collection with filters. If the path
            below 404s, fall back to ``list_controls(filter="control.cid:
            <id>")``.
        """
        return self._gateway(f"/cloudview-api/rest/v1/controls/metadata/{control_id}", method="GET")

    # ------------------------------------------------------------------ #
    # Evaluations (posture)
    # ------------------------------------------------------------------ #
    def list_evaluations(
        self,
        cloud_provider: str,
        account_id: str,
        page_no: int | None = None,
        page_size: int | None = None,
        filter: str | None = None,
        sort: str | None = None,
    ) -> dict[str, Any]:
        """List control evaluations (posture) for a cloud account/subscription/project.

        Args:
            cloud_provider: One of "aws", "azure", "gcp".
            account_id: The cloud account identifier — AWS account ID, Azure
                subscription ID, or GCP project ID.
            page_no: Page number to return (0-based).
            page_size: Number of records per page.
            filter: QQL filter (e.g. ``control.criticality:HIGH and
                evaluation.result:FAIL``).
            sort: Sort expression.

        Returns:
            JSON evaluation list (per-control pass/fail posture) for the
            account, or an error dict.
        """
        provider = self._norm_provider(cloud_provider)
        if not provider:
            return {"error": "cloud_provider must be one of: aws, azure, gcp"}
        params = {"pageNo": page_no, "pageSize": page_size, "filter": filter, "sort": sort}
        return self._gateway(
            f"/cloudview-api/rest/v1/{provider}/evaluations/{account_id}", method="GET", params=params
        )

    def list_control_evaluation_resources(
        self,
        cloud_provider: str,
        account_id: str,
        control_id: str,
        page_no: int | None = None,
        page_size: int | None = None,
        filter: str | None = None,
        sort: str | None = None,
    ) -> dict[str, Any]:
        """List the evaluated resources (pass/fail) for one control in an account.

        Args:
            cloud_provider: One of "aws", "azure", "gcp".
            account_id: AWS account ID, Azure subscription ID, or GCP
                project ID.
            control_id: The control ID (CID) to list evaluated resources for.
            page_no: Page number to return (0-based).
            page_size: Number of records per page.
            filter: QQL filter (e.g. ``evaluation.result:FAIL``).
            sort: Sort expression.

        Returns:
            JSON list of resources with their evaluation result for the
            control, or an error dict.
        """
        provider = self._norm_provider(cloud_provider)
        if not provider:
            return {"error": "cloud_provider must be one of: aws, azure, gcp"}
        params = {"pageNo": page_no, "pageSize": page_size, "filter": filter, "sort": sort}
        return self._gateway(
            f"/cloudview-api/rest/v1/{provider}/evaluations/{account_id}/resources/{control_id}",
            method="GET",
            params=params,
        )

    def get_evaluation_stats(
        self,
        cloud_provider: str,
        control_id: str,
        connector_id: str,
        resource_id: str | None = None,
    ) -> dict[str, Any]:
        """Get evaluation statistics for a control on a connector (optionally one resource).

        Args:
            cloud_provider: One of "aws", "azure", "gcp".
            control_id: The control ID (CID).
            connector_id: The connector ID (UUID) to scope stats to.
            resource_id: Optional resource ID to scope the stats to a single
                resource.

        Returns:
            JSON evaluation stats (pass/fail counts, history), or an error
            dict.
        """
        provider = self._norm_provider(cloud_provider)
        if not provider:
            return {"error": "cloud_provider must be one of: aws, azure, gcp"}
        params = {"resourceId": resource_id}
        return self._gateway(
            f"/cloudview-api/rest/v1/{provider}/evaluations/stats/{control_id}/{connector_id}",
            method="GET",
            params=params,
        )

    # ------------------------------------------------------------------ #
    # Resource inventory
    # ------------------------------------------------------------------ #
    def list_resources(
        self,
        cloud_provider: str,
        resource_type: str,
        page_no: int | None = None,
        page_size: int | None = None,
        filter: str | None = None,
        sort: str | None = None,
        updated: str | None = None,
    ) -> dict[str, Any]:
        """List (and inspect details of) cloud resources of a given type.

        Args:
            cloud_provider: One of "aws", "azure", "gcp". Sent uppercased in
                the path (e.g. "AWS") per the resource inventory API.
            resource_type: Resource type keyword, e.g. (GCP) VM_INSTANCE,
                NETWORK, SUBNETWORK, FIREWALL_RULES, CLOUD_FUNCTION,
                LOAD_BALANCING, K8S_CLUSTER; (AWS) EC2_INSTANCE, S3_BUCKET,
                SECURITY_GROUP, etc. Valid values differ per provider.
            page_no: Page number to return (0-based).
            page_size: Number of records per page.
            filter: QQL filter (e.g. ``resourceId:i-0abc...``). To fetch a
                single resource's details, filter by its resource ID.
            sort: Sort expression, e.g. "lastSyncedOn:desc".
            updated: Date or date range filter on last update
                (YYYY-MM-DD or a range), matching the inventory API.

        Returns:
            JSON resource inventory list (resource configuration details),
            or an error dict.

        Note:
            # TODO(verify): Resource inventory path is
            ``/cloudview-api/rest/v1/resource/{resourceType}/{PROVIDER}``
            (provider segment uppercased). A newer ``rest/v2`` variant with
            marker-based paging also exists. Confirm the resource_type
            keyword set per provider.
        """
        provider = self._norm_provider(cloud_provider)
        if not provider:
            return {"error": "cloud_provider must be one of: aws, azure, gcp"}
        params = {
            "pageNo": page_no,
            "pageSize": page_size,
            "filter": filter,
            "sort": sort,
            "updated": updated,
        }
        return self._gateway(
            f"/cloudview-api/rest/v1/resource/{resource_type}/{provider.upper()}",
            method="GET",
            params=params,
        )

    # ------------------------------------------------------------------ #
    # Policies / mandates
    # ------------------------------------------------------------------ #
    def list_policies(
        self,
        page_no: int | None = None,
        page_size: int | None = None,
        filter: str | None = None,
    ) -> dict[str, Any]:
        """List CloudView policies / mandates (control frameworks).

        Args:
            page_no: Page number to return (0-based).
            page_size: Number of records per page.
            filter: QQL filter string.

        Returns:
            JSON policy/mandate list, or an error dict.

        Note:
            Path confirmed via the TotalCloud 2.13 API notification
            (https://notifications.qualys.com/api/2024/11/13/qualys-cloud-platform-2-13-tc-api-notification-1),
            which introduced ``GET /cloudview-api/rest/v1/mandates`` as the
            current mandates/policy-framework list endpoint, replacing the
            deprecated ``GET /cloudview-api/rest/v1/reports/mandates``. The
            ``/cloudview-api/rest/v1/policy`` guess used previously does not
            exist (404 in the live audit).
        """
        params = {"pageNo": page_no, "pageSize": page_size, "filter": filter}
        return self._gateway("/cloudview-api/rest/v1/mandates", method="GET", params=params)
