"""Patch Management module (Gateway/JWT REST API).

Covers the Qualys Patch Management (PM) APIs on the gateway host (Bearer JWT,
JSON bodies): patch search/details/count, PM asset listing (including assets
missing patches), the patch catalog, and deployment-job lifecycle (list, get,
create, update, enable/disable, delete).

* read  -> search_pm_patches, get_pm_patch, count_pm_patches, list_pm_assets,
           list_patch_catalog, list_deployment_jobs, get_deployment_job
* write -> create_deployment_job, update_deployment_job,
           enable_deployment_job, disable_deployment_job
* destructive -> delete_deployment_job

Endpoints (Swagger: ``gateway.<pod>/apidocs/pm/v1``):
* ``/pm/v2/patches`` (POST search), ``/pm/v1/patches/count`` (GET count)
* ``/pm/v1/patchcatalog/patches``
* ``/pm/v1/assets`` (POST search)
* ``/pm/v1/deploymentjobs`` (list, DELETE), ``/pm/v1/deploymentjob`` (create),
  ``/pm/v1/deploymentjob/{id}`` (get),
  ``/pm/v1/deploymentjob/update/{id}`` (PATCH update / status change)

Docs: https://docs.qualys.com/en/pm/api/ (Patch Management API). Endpoint
versions and body shapes below are best-effort from the release-notes/Swagger
docs and are flagged ``# TODO(verify)`` where uncertain.
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class PatchMgmtModule(BaseModule):
    """Search patches, inspect PM assets, and manage patch deployment jobs."""

    module_label = "patch_mgmt"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(server, self.search_pm_patches, "search_pm_patches", tier="read")
        self._add_tool(server, self.get_pm_patch, "get_pm_patch", tier="read")
        self._add_tool(server, self.count_pm_patches, "count_pm_patches", tier="read")
        self._add_tool(server, self.list_pm_assets, "list_pm_assets", tier="read")
        self._add_tool(server, self.list_patch_catalog, "list_patch_catalog", tier="read")
        self._add_tool(server, self.list_deployment_jobs, "list_deployment_jobs", tier="read")
        self._add_tool(server, self.get_deployment_job, "get_deployment_job", tier="read")
        # Writes
        self._add_tool(server, self.create_deployment_job, "create_deployment_job", tier="write")
        self._add_tool(server, self.update_deployment_job, "update_deployment_job", tier="write")
        self._add_tool(server, self.enable_deployment_job, "enable_deployment_job", tier="write")
        self._add_tool(server, self.disable_deployment_job, "disable_deployment_job", tier="write")
        # Destructive (only registered if enable_destructive)
        self._add_tool(server, self.delete_deployment_job, "delete_deployment_job", tier="destructive")

    # ------------------------------ reads ------------------------------ #
    def search_pm_patches(
        self,
        query: str | None = None,
        having_query: str | None = None,
        attributes: str | None = None,
        platform: str | None = None,
        page_size: int = 100,
    ) -> dict[str, Any]:
        """Search the Patch Management patch inventory using QQL.

        Path/params confirmed against the working PM endpoints in this
        module (``list_pm_assets``/``list_patch_catalog``/
        ``list_deployment_jobs`` all use ``/pm/v1/...``) plus independent
        confirmation of the patches-search call schema (query params
        ``pageSize``/``platform``; POST body ``query``/``havingQuery``/
        ``attributes``): the correct resource is ``POST /pm/v2/patches``, not
        the ``/pm/v3/patches`` guess that 404'd in the live audit.

        Args:
            query: Patch QQL filter (e.g. ``vendorSeverity:Critical and
                platform:Windows``). Omit to match all patches.
            having_query: Secondary QQL applied to the matched set (e.g.
                ``downloadMethod:AcquireFromVendor``).
            attributes: Comma-separated patch attributes to return (e.g.
                "id,title,platform,vendorSeverity"). Omit for the default set.
            platform: Restrict to a platform — "Windows" or "Linux".
            page_size: Max patches per page. Default 100 (PM caps total
                retrievable records at 10,000).

        Returns:
            JSON page of matching patches.
        """
        body: dict[str, Any] = {}
        if query is not None:
            body["query"] = query
        if having_query is not None:
            body["havingQuery"] = having_query
        if attributes is not None:
            body["attributes"] = [a.strip() for a in attributes.split(",") if a.strip()]
        params = {"pageSize": page_size, "platform": platform}
        return self._gateway("/pm/v2/patches", method="POST", params=params, json=body)

    def get_pm_patch(self, patch_uuid: str) -> dict[str, Any]:
        """Get details for a single patch by its UUID.

        Args:
            patch_uuid: The patch UUID (from ``search_pm_patches`` results).

        Returns:
            JSON patch detail record.
        """
        # TODO(verify): not covered by the live audit (skipped — needs
        # patch_uuid). Given search_pm_patches is confirmed to live under
        # /pm/v2/patches (not /pm/v3), this single-patch GET path is likely
        # also wrong, but no confirmed single-patch-by-uuid endpoint was
        # found in the docs reviewed for this fix — left unchanged pending
        # verification against a live console.
        return self._gateway(f"/pm/v3/patches/{patch_uuid}", method="GET")

    def count_pm_patches(
        self,
        query: str | None = None,
        having_query: str | None = None,
        platform: str | None = None,
    ) -> dict[str, Any]:
        """Count Patch Management patches matching a QQL filter (no rows returned).

        Path/method confirmed via the Patch Management API guide's "Get
        Patch Count"
        (https://docs.qualys.com/en/pm/api/scan_result_patch_resource/get_patch_count.htm):
        ``GET /pm/v1/patches/count`` with query params (not the
        ``POST /pm/v3/patches/count`` with a JSON body previously assumed
        here, which 404'd in the live audit).

        Args:
            query: Patch QQL filter. Omit to count all patches.
            having_query: Secondary QQL applied to the matched set.
            platform: Restrict to a platform — "Windows" or "Linux".

        Returns:
            JSON with the patch count.
        """
        params = {"query": query, "havingQuery": having_query, "platform": platform}
        return self._gateway("/pm/v1/patches/count", method="GET", params=params)

    def list_pm_assets(
        self,
        query: str | None = None,
        having_query: str | None = None,
        attributes: str | None = None,
        platform: str | None = None,
        page_size: int = 100,
        sort_order: str | None = None,
        search_after: str | None = None,
    ) -> dict[str, Any]:
        """List Patch Management assets, optionally filtered by QQL.

        To list assets that are missing patches, filter with a QQL such as
        ``missingPatchCount>0`` (or ``installedPatchCount>1`` for installed).

        Args:
            query: Asset QQL filter (e.g. "missingPatchCount>0"). Omit to
                match all PM assets.
            having_query: Secondary QQL applied to the matched set (e.g.
                "downloadMethod:AcquireFromVendor and rebootRequired:true").
            attributes: Comma-separated asset attributes to return (e.g.
                "name,id,platform"). Omit for the default set.
            platform: Restrict to a platform — "Windows" or "Linux".
            page_size: Max assets per page. Default 100.
            sort_order: "ASC" or "DESC".
            search_after: Cursor for keyset pagination, "asset_name,asset_id"
                from the previous page's last record.

        Returns:
            JSON page of matching PM assets.
        """
        body: dict[str, Any] = {}
        if query is not None:
            body["query"] = query
        if having_query is not None:
            body["havingQuery"] = having_query
        if attributes is not None:
            body["attributes"] = attributes
        params = {
            "platform": platform,
            "pageSize": page_size,
            "sortOrder": sort_order,
            "searchAfter": search_after,
        }
        return self._gateway("/pm/v1/assets", method="POST", params=params, json=body)

    def list_patch_catalog(
        self,
        platform: str | None = None,
        query: str | None = None,
        page_size: int = 100,
        page_number: int = 0,
    ) -> dict[str, Any]:
        """List patches from the Patch Management catalog (Windows/Linux).

        Args:
            platform: Restrict to a platform — "Windows" or "Linux".
            query: Optional QQL filter over catalog patches.
                # TODO(verify): confirm the catalog filter param/mechanism.
            page_size: Max catalog patches per page. Default 100.
            page_number: Zero-based page index.

        Returns:
            JSON page of catalog patch records.
        """
        # TODO(verify): confirm /pm/v1/patchcatalog/patches path and whether it is GET+params or POST+body.
        params = {
            "platform": platform,
            "query": query,
            "pageSize": page_size,
            "pageNumber": page_number,
        }
        return self._gateway("/pm/v1/patchcatalog/patches", method="GET", params=params)

    def list_deployment_jobs(
        self,
        query: str | None = None,
        platform: str | None = None,
        page_number: int = 0,
        page_size: int = 100,
        sort: str | None = None,
    ) -> dict[str, Any]:
        """List patch deployment jobs in the subscription.

        Args:
            query: Optional QQL filter over jobs (e.g. by name/status).
                # TODO(verify): confirm the job filter param name.
            platform: Restrict to a platform — "Windows" or "Linux".
            page_number: Zero-based page index.
            page_size: Max jobs per page. Default 100.
            sort: Sort spec (e.g. "createdDate:desc").
                # TODO(verify): confirm sort syntax.

        Returns:
            JSON page of deployment jobs.
        """
        params = {
            "query": query,
            "platform": platform,
            "pageNumber": page_number,
            "pageSize": page_size,
            "sort": sort,
        }
        return self._gateway("/pm/v1/deploymentjobs", method="GET", params=params)

    def get_deployment_job(self, job_id: str) -> dict[str, Any]:
        """Get the full configuration of a single deployment job.

        Args:
            job_id: The deployment job ID (UUID).

        Returns:
            JSON deployment-job detail record.
        """
        return self._gateway(f"/pm/v1/deploymentjob/{job_id}", method="GET")

    # ------------------------------ writes ----------------------------- #
    def create_deployment_job(
        self,
        name: str,
        platform: str,
        job_type: str | None = None,
        approved_patches: str | None = None,
        asset_ids: str | None = None,
        asset_tag_ids: str | None = None,
        dynamic_patches_qql: str | None = None,
        is_dynamic_patches_qql: bool | None = None,
        schedule_type: str | None = None,
        description: str | None = None,
        status: str | None = None,
        extra_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a patch deployment job.

        Args:
            name: Name of the deployment job.
            platform: Target platform — "Windows" or "Linux".
            job_type: Job type, e.g. "Install" or "Rollback" (Windows) /
                "Uninstall". # TODO(verify): confirm enum values.
            approved_patches: Comma-separated patch UUIDs to deploy.
            asset_ids: Comma-separated asset IDs to target.
            asset_tag_ids: Comma-separated asset tag IDs to target.
            dynamic_patches_qql: QQL selecting patches dynamically at run time.
            is_dynamic_patches_qql: True to treat dynamic_patches_qql as the
                patch source (dynamic job).
            schedule_type: Scheduling type, e.g. "ON_DEMAND", "DAILY",
                "WEEKLY", "MONTHLY". # TODO(verify): confirm enum + required
                schedule sub-fields (pass via extra_config).
            description: Free-text description of the job.
            status: Initial status, "Enabled" or "Disabled".
            extra_config: Optional advanced config merged into the request
                body verbatim — e.g. ``preDeployment``, ``duringDeployment``,
                ``postDeployment``, ``schedule``, ``recurring`` blocks.
                # TODO(verify): confirm exact nested schema.

        Returns:
            JSON with the created job (including its ID), or an error dict.
        """
        # TODO(verify): confirm /pm/v1/deploymentjob create body field names.
        body: dict[str, Any] = {"name": name, "platform": platform}
        if job_type is not None:
            body["type"] = job_type
        if approved_patches is not None:
            body["approvedPatches"] = [p.strip() for p in approved_patches.split(",") if p.strip()]
        if asset_ids is not None:
            body["assetIds"] = [a.strip() for a in asset_ids.split(",") if a.strip()]
        if asset_tag_ids is not None:
            body["assetTagIds"] = [t.strip() for t in asset_tag_ids.split(",") if t.strip()]
        if dynamic_patches_qql is not None:
            body["dynamicPatchesQQL"] = dynamic_patches_qql
        if is_dynamic_patches_qql is not None:
            body["isDynamicPatchesQQL"] = is_dynamic_patches_qql
        if schedule_type is not None:
            body["scheduleType"] = schedule_type
        if description is not None:
            body["description"] = description
        if status is not None:
            body["status"] = status
        if extra_config:
            body.update(extra_config)
        return self._gateway("/pm/v1/deploymentjob", method="POST", json=body)

    def update_deployment_job(
        self,
        job_id: str,
        name: str | None = None,
        approved_patches: str | None = None,
        asset_ids: str | None = None,
        asset_tag_ids: str | None = None,
        dynamic_patches_qql: str | None = None,
        description: str | None = None,
        status: str | None = None,
        extra_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update an existing patch deployment job.

        Args:
            job_id: The deployment job ID (UUID) to update.
            name: New name for the job.
            approved_patches: Comma-separated patch UUIDs to set on the job.
            asset_ids: Comma-separated asset IDs to set as targets.
            asset_tag_ids: Comma-separated asset tag IDs to set as targets.
            dynamic_patches_qql: QQL selecting patches dynamically at run time.
            description: New description.
            status: "Enabled" or "Disabled".
            extra_config: Optional advanced config merged into the request
                body verbatim (schedule/recurring/deployment blocks).

        Returns:
            JSON with the updated job, or an error dict.
        """
        # TODO(verify): confirm PATCH /pm/v1/deploymentjob/update/{id} body field names.
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if approved_patches is not None:
            body["approvedPatches"] = [p.strip() for p in approved_patches.split(",") if p.strip()]
        if asset_ids is not None:
            body["assetIds"] = [a.strip() for a in asset_ids.split(",") if a.strip()]
        if asset_tag_ids is not None:
            body["assetTagIds"] = [t.strip() for t in asset_tag_ids.split(",") if t.strip()]
        if dynamic_patches_qql is not None:
            body["dynamicPatchesQQL"] = dynamic_patches_qql
        if description is not None:
            body["description"] = description
        if status is not None:
            body["status"] = status
        if extra_config:
            body.update(extra_config)
        return self._gateway(f"/pm/v1/deploymentjob/update/{job_id}", method="PATCH", json=body)

    def enable_deployment_job(self, job_id: str) -> dict[str, Any]:
        """Enable (activate) a patch deployment job.

        Args:
            job_id: The deployment job ID (UUID) to enable.

        Returns:
            JSON with the updated job status, or an error dict.
        """
        # TODO(verify): confirm status change is via PATCH update with {"status": "Enabled"}.
        return self._gateway(
            f"/pm/v1/deploymentjob/update/{job_id}", method="PATCH", json={"status": "Enabled"}
        )

    def disable_deployment_job(self, job_id: str) -> dict[str, Any]:
        """Disable (deactivate) a patch deployment job.

        Args:
            job_id: The deployment job ID (UUID) to disable.

        Returns:
            JSON with the updated job status, or an error dict.
        """
        # TODO(verify): confirm status change is via PATCH update with {"status": "Disabled"}.
        return self._gateway(
            f"/pm/v1/deploymentjob/update/{job_id}", method="PATCH", json={"status": "Disabled"}
        )

    # --------------------------- destructive --------------------------- #
    def delete_deployment_job(self, job_ids: str, confirm: str | None = None) -> dict[str, Any]:
        """Permanently delete one or more patch deployment jobs. IRREVERSIBLE.

        Gated: requires the console to be started with QUALYS_ENABLE_DESTRUCTIVE
        and the caller to pass confirm=<job_ids>.

        Args:
            job_ids: Comma-separated deployment job ID(s) (UUIDs) to delete.
            confirm: Must equal ``job_ids`` to proceed.

        Returns:
            JSON delete result, or a confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=job_ids)
        if guard:
            return guard
        # TODO(verify): confirm DELETE /pm/v1/deploymentjobs body shape (list vs {"jobIds": [...]}).
        ids = [j.strip() for j in job_ids.split(",") if j.strip()]
        return self._gateway("/pm/v1/deploymentjobs", method="DELETE", json=ids)
