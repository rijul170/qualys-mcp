"""CyberSecurity Asset Management (CSAM) module.

Richer asset-inventory reads plus asset tagging over the CSAM/GAV shared
inventory backend. Read operations use the gateway host (Bearer JWT, GAV/CSAM
v2 ``/rest/2.0/.../am/asset`` endpoints). Tag assignment/removal uses the
Qualys Asset Management & Tagging API (QPS regime, XML body), which is the
supported mechanism for changing tags on assets.

* read  -> search_csam_assets, get_csam_asset, count_csam_assets,
           list_csam_software, list_csam_asset_tags
* write -> add_csam_asset_tags, remove_csam_asset_tags

Endpoints:
* Gateway: ``POST /rest/2.0/search/am/asset``, ``GET /rest/2.0/get/am/asset``,
  ``POST /rest/2.0/count/am/asset``, ``POST /rest/2.0/am/asset/component``
* QPS:     ``POST /qps/rest/2.0/update/am/hostasset/`` (tag add/remove)

Docs: https://docs.qualys.com/en/csam/api/ (CSAM/GAV API v2) and the Qualys
Asset Management & Tagging API v2 guide.

# TODO(verify): CSAM and GAV share the ``/rest/2.0/.../am/asset`` backend, so
# search/get/count overlap with ``gav.py``. This module carries the richer
# search (QQL), software inventory, and tagging; GAV carries the basic reads.
# TODO(verify): The GAV/CSAM v2 API documents search/count *filters* in an XML
# ``<FilterRequest>`` body; the JSON-only gateway wrapper here sends JSON, so
# the filter-body shape is best-effort.
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


def _xml_escape(value: Any) -> str:
    """Escape a value for safe inclusion as XML text/attribute content."""
    text = str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


class CsamModule(BaseModule):
    """Search/inspect the CSAM asset inventory and manage user-defined asset tags."""

    module_label = "csam"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(server, self.search_csam_assets, "search_csam_assets", tier="read")
        self._add_tool(server, self.get_csam_asset, "get_csam_asset", tier="read")
        self._add_tool(server, self.count_csam_assets, "count_csam_assets", tier="read")
        self._add_tool(server, self.list_csam_software, "list_csam_software", tier="read")
        self._add_tool(server, self.list_csam_asset_tags, "list_csam_asset_tags", tier="read")
        # Writes
        self._add_tool(server, self.add_csam_asset_tags, "add_csam_asset_tags", tier="write")
        self._add_tool(server, self.remove_csam_asset_tags, "remove_csam_asset_tags", tier="write")

    # ------------------------------ reads ------------------------------ #
    def search_csam_assets(
        self,
        filter_qql: str | None = None,
        page_size: int = 100,
        last_seen_asset_id: int | None = None,
        asset_last_updated: str | None = None,
        include_fields: str | None = None,
    ) -> dict[str, Any]:
        """Search the CyberSecurity Asset Management inventory using QQL.

        Args:
            filter_qql: QQL filter (e.g. "operatingSystem:Windows and
                tagName:Production"). Omit to match all assets.
            page_size: Max assets per page. Default 100.
            last_seen_asset_id: Keyset-pagination cursor — pass the highest
                asset ID from the previous page to fetch the next page.
            asset_last_updated: Only assets updated on/after this datetime,
                ISO 8601 UTC (YYYY-MM-DDTHH:MM:SSZ).
            include_fields: Comma-separated asset fields to include in the
                response (e.g. "software,openPorts,tags"). Omit for defaults.
                # TODO(verify): confirm the field-selection param name.

        Returns:
            JSON page of matching assets plus paging metadata.
        """
        # TODO(verify): confirm JSON filter body key vs XML <FilterRequest> body.
        params = {
            "pageSize": page_size,
            "lastSeenAssetId": last_seen_asset_id,
            "assetLastUpdated": asset_last_updated,
            "includeFields": include_fields,
        }
        body: dict[str, Any] = {"filter": filter_qql} if filter_qql else {}
        return self._gateway(
            "/rest/2.0/search/am/asset", method="POST", params=params, json=body or None
        )

    def get_csam_asset(self, asset_id: int) -> dict[str, Any]:
        """Get full CSAM detail for a single asset by ID.

        Args:
            asset_id: The CSAM/GAV asset ID.

        Returns:
            JSON asset detail record (hardware/OS, services, open ports,
            installed software, user accounts, tags, business context).
        """
        return self._gateway("/rest/2.0/get/am/asset", method="GET", params={"assetId": asset_id})

    def count_csam_assets(self, filter_qql: str | None = None) -> dict[str, Any]:
        """Count CSAM assets matching a QQL filter (no result rows returned).

        Args:
            filter_qql: Optional QQL filter. Omit to count all assets.

        Returns:
            JSON with the matching asset count.
        """
        body: dict[str, Any] = {"filter": filter_qql} if filter_qql else {}
        return self._gateway("/rest/2.0/count/am/asset", method="POST", json=body or None)

    def list_csam_software(
        self,
        asset_id: int | None = None,
        filter_qql: str | None = None,
        page_size: int = 100,
    ) -> dict[str, Any]:
        """List installed software (components) across assets or for one asset.

        Args:
            asset_id: Restrict to software installed on this asset. When
                omitted, returns software across all matching assets.
            filter_qql: Optional QQL filter over software components (e.g.
                "software:(name:'OpenSSL')").
            page_size: Max software rows per page. Default 100.

        Returns:
            JSON page of software component records.
        """
        # TODO(verify): confirm /rest/2.0/am/asset/component[/{assetId}] path,
        # method, and filter body shape.
        params = {"pageSize": page_size}
        body: dict[str, Any] = {"filter": filter_qql} if filter_qql else {}
        path = "/rest/2.0/am/asset/component"
        if asset_id is not None:
            path = f"/rest/2.0/am/asset/component/{asset_id}"
        return self._gateway(path, method="POST", params=params, json=body or None)

    def list_csam_asset_tags(self, asset_id: int) -> dict[str, Any]:
        """List the tags currently assigned to a specific CSAM asset.

        Args:
            asset_id: The CSAM/GAV asset ID whose assigned tags to return.

        Returns:
            JSON asset detail whose ``tags``/``tagList`` block enumerates the
            tags assigned to the asset.
        """
        # TODO(verify): CSAM surfaces assigned tags inline on the asset record;
        # confirm there is no dedicated per-asset tag endpoint to prefer.
        return self._gateway("/rest/2.0/get/am/asset", method="GET", params={"assetId": asset_id})

    # ------------------------------ writes ----------------------------- #
    def _tag_update_body(self, asset_ids: str, tag_ids: str, operation: str) -> str:
        """Build a QPS ``<ServiceRequest>`` body to add/remove tags on assets.

        Args:
            asset_ids: Comma-separated asset IDs to update.
            tag_ids: Comma-separated tag IDs to add or remove.
            operation: "add" or "remove".

        Returns:
            A ServiceRequest XML string.
        """
        id_csv = ",".join(a.strip() for a in asset_ids.split(",") if a.strip())
        tags_xml = "".join(
            f"<TagSimple><id>{_xml_escape(t.strip())}</id></TagSimple>"
            for t in tag_ids.split(",")
            if t.strip()
        )
        return (
            "<ServiceRequest>"
            "<filters>"
            f'<Criteria field="id" operator="IN">{_xml_escape(id_csv)}</Criteria>'
            "</filters>"
            "<data><HostAsset><tags>"
            f"<{operation}>{tags_xml}</{operation}>"
            "</tags></HostAsset></data>"
            "</ServiceRequest>"
        )

    def add_csam_asset_tags(self, asset_ids: str, tag_ids: str) -> dict[str, Any]:
        """Assign one or more user-defined tags to one or more assets.

        Uses the Asset Management & Tagging API (QPS). Up to 10,000 assets can
        be updated per call.

        Args:
            asset_ids: Comma-separated asset IDs to tag.
            tag_ids: Comma-separated tag IDs to assign.

        Returns:
            Parsed QPS ServiceResponse (updated asset count/records), or an
            error dict.
        """
        # TODO(verify): confirm QPS endpoint (am/hostasset vs am/asset) and
        # that <tags><add><TagSimple><id> is the correct assign structure.
        body = self._tag_update_body(asset_ids, tag_ids, "add")
        return self._qps("/qps/rest/2.0/update/am/hostasset/", method="POST", body_xml=body)

    def remove_csam_asset_tags(self, asset_ids: str, tag_ids: str) -> dict[str, Any]:
        """Remove one or more user-defined tags from one or more assets.

        Uses the Asset Management & Tagging API (QPS). Up to 10,000 assets can
        be updated per call.

        Args:
            asset_ids: Comma-separated asset IDs to update.
            tag_ids: Comma-separated tag IDs to remove.

        Returns:
            Parsed QPS ServiceResponse (updated asset count/records), or an
            error dict.
        """
        # TODO(verify): confirm QPS endpoint and that <tags><remove><TagSimple>
        # <id> is the correct removal structure.
        body = self._tag_update_body(asset_ids, tag_ids, "remove")
        return self._qps("/qps/rest/2.0/update/am/hostasset/", method="POST", body_xml=body)
