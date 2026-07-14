"""Global AssetView (GAV) module (Gateway/JWT REST API) — asset inventory, read-only.

Basic asset-inventory reads over the Global AssetView / CyberSecurity Asset
Management shared inventory backend, on the gateway host (Bearer JWT):
list/search all assets, get an asset by ID, count assets, and list a host's
software instances.

* read -> list_gav_assets, get_gav_asset, count_gav_assets,
          list_gav_host_instances

Endpoints (GAV/CSAM v2, gateway host):
* ``POST /rest/2.0/search/am/asset``
* ``GET  /rest/2.0/get/am/asset?assetId=...``
* ``POST /rest/2.0/count/am/asset``
* ``GET  /am/v2/sn/assets/host/{assetId}``

Docs: https://docs.qualys.com/en/csam/api/ (GAV/CSAM API v2).

# TODO(verify): GAV and CSAM share the same ``/rest/2.0/.../am/asset``
# inventory backend, so these endpoints overlap with the CSAM module — this
# module is intentionally limited to the basic read set while richer search
# and tagging live in ``csam.py``.
# TODO(verify): The GAV/CSAM v2 API documents its search/count *filters* in an
# XML ``<FilterRequest>`` request body. The gateway wrapper here sends JSON
# bodies only, so the ``filters``/pagination shapes below are best-effort; if
# the console rejects JSON filters, filtering must move to an XML body
# (unsupported by the JSON-only gateway wrapper) or query parameters.
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class GavModule(BaseModule):
    """Read-only Global AssetView asset inventory over the gateway API."""

    module_label = "gav"

    def register_tools(self, server: FastMCP) -> None:
        self._add_tool(server, self.list_gav_assets, "list_gav_assets", tier="read")
        self._add_tool(server, self.get_gav_asset, "get_gav_asset", tier="read")
        self._add_tool(server, self.count_gav_assets, "count_gav_assets", tier="read")
        self._add_tool(
            server, self.list_gav_host_instances, "list_gav_host_instances", tier="read"
        )

    def _filter_body(self, filter_qql: str | None) -> dict[str, Any]:
        """Build a best-effort JSON filter body from a QQL string.

        Args:
            filter_qql: A QQL filter string (e.g. ``operatingSystem:Windows``).

        Returns:
            A JSON body dict; empty when no filter is supplied.
        """
        # TODO(verify): confirm the JSON key for the QQL filter ("filter" vs
        # "filters" vs an XML <FilterRequest> body) on the target console.
        return {"filter": filter_qql} if filter_qql else {}

    def list_gav_assets(
        self,
        filter_qql: str | None = None,
        page_size: int = 100,
        last_seen_asset_id: int | None = None,
        asset_last_updated: str | None = None,
    ) -> dict[str, Any]:
        """List/search all assets in the Global AssetView inventory.

        Args:
            filter_qql: Optional QQL filter (e.g. "operatingSystem:Windows" or
                "tagName:Production"). Omit to list all assets.
            page_size: Max assets per page. Default 100.
            last_seen_asset_id: Keyset-pagination cursor — pass the highest
                asset ID from the previous page to fetch the next page.
            asset_last_updated: Only assets updated on/after this datetime,
                ISO 8601 UTC (YYYY-MM-DDTHH:MM:SSZ).

        Returns:
            JSON page of assets (asset list plus paging metadata).
        """
        params = {
            "pageSize": page_size,
            "lastSeenAssetId": last_seen_asset_id,
            "assetLastUpdated": asset_last_updated,
        }
        body = self._filter_body(filter_qql)
        return self._gateway(
            "/rest/2.0/search/am/asset", method="POST", params=params, json=body or None
        )

    def get_gav_asset(self, asset_id: int) -> dict[str, Any]:
        """Get full detail for a single asset by its GAV asset ID.

        Args:
            asset_id: The GAV/CSAM asset ID.

        Returns:
            JSON asset detail record.
        """
        return self._gateway("/rest/2.0/get/am/asset", method="GET", params={"assetId": asset_id})

    def count_gav_assets(self, filter_qql: str | None = None) -> dict[str, Any]:
        """Count assets in the Global AssetView inventory matching a QQL filter.

        Args:
            filter_qql: Optional QQL filter. Omit to count all assets.

        Returns:
            JSON with the matching asset count.
        """
        body = self._filter_body(filter_qql)
        return self._gateway("/rest/2.0/count/am/asset", method="POST", json=body or None)

    def list_gav_host_instances(self, asset_id: int) -> dict[str, Any]:
        """List the software instances reported for a host asset.

        Args:
            asset_id: The GAV/CSAM host asset ID.

        Returns:
            JSON host detail including per-software instances (name, version,
            port, paths, first/last seen).
        """
        # TODO(verify): confirm /am/v2/sn/assets/host/{assetId} path and response shape.
        return self._gateway(f"/am/v2/sn/assets/host/{asset_id}", method="GET")
