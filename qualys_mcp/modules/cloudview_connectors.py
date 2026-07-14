"""TotalCloud / CloudView — Cloud Connectors module (Gateway/JWT REST API).

Covers CSPM cloud connector management for AWS, Azure, and GCP: listing,
fetching, creating, updating, on-demand sync ("run"), and deleting connectors
that gather resource inventory and evaluate posture.

All endpoints are on the Gateway host under ``/cloudview-api/rest/v1/...`` and
use JWT bearer auth (auto-fetched by ``self._gateway``). Request bodies are
JSON.

Docs: Qualys TotalCloud / CloudView API User Guide — "Connectors"
(AWS/Azure/GCP). https://docs.qualys.com/en/tc/api/
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule

# Providers that map 1:1 to a path segment under /cloudview-api/rest/v1/.
_PROVIDERS = ("aws", "azure", "gcp")


class CloudviewConnectorsModule(BaseModule):
    """Manage TotalCloud/CloudView cloud connectors (AWS, Azure, GCP)."""

    module_label = "cloudview_connectors"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(server, self.list_cloud_connectors, "list_cloud_connectors", tier="read")
        self._add_tool(server, self.get_cloud_connector, "get_cloud_connector", tier="read")
        # Writes
        self._add_tool(server, self.create_aws_connector, "create_aws_connector", tier="write")
        self._add_tool(server, self.create_azure_connector, "create_azure_connector", tier="write")
        self._add_tool(server, self.create_gcp_connector, "create_gcp_connector", tier="write")
        self._add_tool(server, self.update_cloud_connector, "update_cloud_connector", tier="write")
        self._add_tool(server, self.run_connector_sync, "run_connector_sync", tier="write")
        # Destructive
        self._add_tool(server, self.delete_cloud_connector, "delete_cloud_connector", tier="destructive")

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _norm_provider(cloud_provider: str) -> str | None:
        p = cloud_provider.lower().strip()
        return p if p in _PROVIDERS else None

    # ------------------------------------------------------------------ #
    # Reads
    # ------------------------------------------------------------------ #
    def list_cloud_connectors(
        self,
        cloud_provider: str,
        page_no: int | None = None,
        page_size: int | None = None,
        filter: str | None = None,
        sort: str | None = None,
    ) -> dict[str, Any]:
        """List cloud connectors for a provider.

        Args:
            cloud_provider: One of "aws", "azure", "gcp".
            page_no: Page number to return (0-based).
            page_size: Number of records per page.
            filter: Qualys Query Language (QQL) filter string
                (e.g. ``name:MyConnector``).
            sort: Sort expression, e.g. "name:asc" or "lastSyncedOn:desc".

        Returns:
            JSON connector list envelope (typically ``content`` array plus
            paging metadata), or a standardized error dict.
        """
        provider = self._norm_provider(cloud_provider)
        if not provider:
            return {"error": "cloud_provider must be one of: aws, azure, gcp"}
        params = {
            "pageNo": page_no,
            "pageSize": page_size,
            "filter": filter,
            "sort": sort,
        }
        return self._gateway(f"/cloudview-api/rest/v1/{provider}/connectors", method="GET", params=params)

    def get_cloud_connector(self, cloud_provider: str, connector_id: str) -> dict[str, Any]:
        """Get details for a single cloud connector.

        Args:
            cloud_provider: One of "aws", "azure", "gcp".
            connector_id: The connector ID (UUID) to fetch.

        Returns:
            JSON connector detail, or a standardized error dict.
        """
        provider = self._norm_provider(cloud_provider)
        if not provider:
            return {"error": "cloud_provider must be one of: aws, azure, gcp"}
        return self._gateway(
            f"/cloudview-api/rest/v1/{provider}/connectors/{connector_id}", method="GET"
        )

    # ------------------------------------------------------------------ #
    # Writes — create
    # ------------------------------------------------------------------ #
    def create_aws_connector(
        self,
        name: str,
        arn: str,
        external_id: str,
        description: str | None = None,
        all_regions: bool | None = None,
        is_gov_cloud: bool | None = None,
        is_china_region: bool | None = None,
        disabled: bool | None = None,
        group_ids: str | None = None,
        additional_fields: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new AWS cloud connector (cross-account IAM role based).

        Args:
            name: Connector name.
            arn: The AWS IAM role ARN Qualys assumes for read access
                (e.g. "arn:aws:iam::123456789012:role/Qualys-Role").
            external_id: The external ID used in the IAM role trust policy.
                Fetch a Qualys-generated base account/external ID first if
                your workflow requires it.
            description: Optional connector description.
            all_regions: Sync resources across all AWS regions when True.
            is_gov_cloud: Set True for AWS GovCloud accounts.
            is_china_region: Set True for AWS China accounts.
            disabled: Create the connector in a disabled state when True.
            group_ids: Comma-separated connector group IDs to add the
                connector to.
            additional_fields: Escape hatch for any documented body fields
                not exposed above (merged into the request body verbatim).

        Returns:
            JSON create result (usually the new connector), or an error dict.

        Note:
            # TODO(verify): Exact AWS connector create body field names
            (arn/externalId/allRegions/isGovCloudConfigured/etc.) vary by
            TotalCloud/Connector release. Confirm against the current
            AWS connector v1 create schema.
        """
        body: dict[str, Any] = {"name": name, "arn": arn, "externalId": external_id}
        if description is not None:
            body["description"] = description
        if all_regions is not None:
            body["allRegions"] = all_regions
        if is_gov_cloud is not None:
            body["isGovCloudConfigured"] = is_gov_cloud
        if is_china_region is not None:
            body["isChinaRegion"] = is_china_region
        if disabled is not None:
            body["disabled"] = disabled
        if group_ids:
            body["groupIds"] = [g.strip() for g in group_ids.split(",") if g.strip()]
        if additional_fields:
            body.update(additional_fields)
        return self._gateway("/cloudview-api/rest/v1/aws/connectors", method="POST", json=body)

    def create_azure_connector(
        self,
        name: str,
        subscription_id: str,
        directory_id: str,
        application_id: str,
        authentication_key: str,
        description: str | None = None,
        disabled: bool | None = None,
        group_ids: str | None = None,
        additional_fields: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new Azure cloud connector (service principal based).

        Args:
            name: Connector name.
            subscription_id: Azure subscription ID to onboard.
            directory_id: Azure AD directory (tenant) ID.
            application_id: Azure AD application (client) ID of the service
                principal Qualys uses.
            authentication_key: The service principal client secret /
                authentication key.
            description: Optional connector description.
            disabled: Create the connector in a disabled state when True.
            group_ids: Comma-separated connector group IDs.
            additional_fields: Escape hatch for any documented body fields
                not exposed above (merged into the request body verbatim).

        Returns:
            JSON create result, or an error dict.

        Note:
            # TODO(verify): Azure connector create body field names
            (subscriptionId/directoryId/applicationId/authenticationKey)
            differ across releases (tenantId/clientId/clientSecret in some).
            Confirm against the current Azure connector v1 create schema.
        """
        body: dict[str, Any] = {
            "name": name,
            "subscriptionId": subscription_id,
            "directoryId": directory_id,
            "applicationId": application_id,
            "authenticationKey": authentication_key,
        }
        if description is not None:
            body["description"] = description
        if disabled is not None:
            body["disabled"] = disabled
        if group_ids:
            body["groupIds"] = [g.strip() for g in group_ids.split(",") if g.strip()]
        if additional_fields:
            body.update(additional_fields)
        return self._gateway("/cloudview-api/rest/v1/azure/connectors", method="POST", json=body)

    def create_gcp_connector(
        self,
        name: str,
        project_id: str,
        credentials_json: str,
        description: str | None = None,
        disabled: bool | None = None,
        group_ids: str | None = None,
        additional_fields: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new GCP cloud connector (service account key based).

        Args:
            name: Connector name.
            project_id: GCP project ID to onboard.
            credentials_json: The GCP service account key material (the JSON
                key contents) Qualys uses to read the project.
            description: Optional connector description.
            disabled: Create the connector in a disabled state when True.
            group_ids: Comma-separated connector group IDs.
            additional_fields: Escape hatch for any documented body fields
                not exposed above (merged into the request body verbatim).

        Returns:
            JSON create result, or an error dict.

        Note:
            # TODO(verify): GCP connector create body shape — whether the
            service account key is sent as a single ``credentials`` string,
            a nested object, or discrete fields (privateKey/clientEmail/
            projectId) — varies by release. Confirm against the current GCP
            connector v1 create schema.
        """
        body: dict[str, Any] = {
            "name": name,
            "projectId": project_id,
            "credentials": credentials_json,
        }
        if description is not None:
            body["description"] = description
        if disabled is not None:
            body["disabled"] = disabled
        if group_ids:
            body["groupIds"] = [g.strip() for g in group_ids.split(",") if g.strip()]
        if additional_fields:
            body.update(additional_fields)
        return self._gateway("/cloudview-api/rest/v1/gcp/connectors", method="POST", json=body)

    # ------------------------------------------------------------------ #
    # Writes — update / run
    # ------------------------------------------------------------------ #
    def update_cloud_connector(
        self,
        cloud_provider: str,
        connector_id: str,
        name: str | None = None,
        description: str | None = None,
        disabled: bool | None = None,
        all_regions: bool | None = None,
        fields: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update an existing cloud connector.

        Args:
            cloud_provider: One of "aws", "azure", "gcp".
            connector_id: The connector ID (UUID) to update.
            name: New connector name.
            description: New connector description.
            disabled: Enable (False) or disable (True) the connector.
            all_regions: (AWS) Toggle syncing across all regions.
            fields: Escape hatch for any additional documented body fields to
                update (merged verbatim, e.g. updated credentials for
                Azure/GCP or a new role ARN for AWS).

        Returns:
            JSON update result, or an error dict.

        Note:
            # TODO(verify): The update body typically must echo required
            provider-specific fields (e.g. AWS arn/externalId), not only the
            changed ones. Use ``fields`` to supply them if a partial update
            is rejected. Confirm the update semantics per provider.
        """
        provider = self._norm_provider(cloud_provider)
        if not provider:
            return {"error": "cloud_provider must be one of: aws, azure, gcp"}
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        if disabled is not None:
            body["disabled"] = disabled
        if all_regions is not None:
            body["allRegions"] = all_regions
        if fields:
            body.update(fields)
        return self._gateway(
            f"/cloudview-api/rest/v1/{provider}/connectors/{connector_id}", method="PUT", json=body
        )

    def run_connector_sync(self, cloud_provider: str, connector_ids: str) -> dict[str, Any]:
        """Trigger an on-demand sync ("run") for one or more connectors.

        Args:
            cloud_provider: One of "aws", "azure", "gcp".
            connector_ids: Comma-separated connector ID(s) to run.

        Returns:
            JSON run result, or an error dict.

        Note:
            # TODO(verify): The run endpoint is ``POST
            /cloudview-api/rest/v1/{provider}/connectors/run``; confirm
            whether the connector IDs go in the JSON body (e.g.
            ``{"connectorIds": [...]}``) or as query parameters for your
            release.
        """
        provider = self._norm_provider(cloud_provider)
        if not provider:
            return {"error": "cloud_provider must be one of: aws, azure, gcp"}
        ids = [c.strip() for c in connector_ids.split(",") if c.strip()]
        body = {"connectorIds": ids}
        return self._gateway(f"/cloudview-api/rest/v1/{provider}/connectors/run", method="POST", json=body)

    # ------------------------------------------------------------------ #
    # Destructive
    # ------------------------------------------------------------------ #
    def delete_cloud_connector(
        self, cloud_provider: str, connector_id: str, confirm: str | None = None
    ) -> dict[str, Any]:
        """Permanently delete a cloud connector. IRREVERSIBLE.

        Args:
            cloud_provider: One of "aws", "azure", "gcp".
            connector_id: The connector ID (UUID) to delete.
            confirm: Must equal ``connector_id`` to proceed.

        Returns:
            JSON delete result (often empty on success), or a
            confirmation/error dict.

        Note:
            # TODO(verify): Some releases expose delete as a bulk operation
            (``DELETE /cloudview-api/rest/v1/{provider}/connectors`` with a
            body/query list of IDs) rather than a per-ID path. This uses the
            per-connector path form; confirm against the current schema.
        """
        provider = self._norm_provider(cloud_provider)
        if not provider:
            return {"error": "cloud_provider must be one of: aws, azure, gcp"}
        guard = self._confirm_or_error(confirm, expected=connector_id)
        if guard:
            return guard
        return self._gateway(
            f"/cloudview-api/rest/v1/{provider}/connectors/{connector_id}", method="DELETE"
        )
