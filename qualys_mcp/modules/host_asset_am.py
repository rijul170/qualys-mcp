"""Host Asset (AM) module (QPS REST API) — normalized asset inventory, read-focused.

Search and fetch assets from Qualys's normalized Asset Management (AM)
inventory: the host-specific view (``am/hostasset``) and the generic
cross-type view (``am/asset``, which can include non-host asset types
depending on the subscription's enabled modules).

Endpoints:
* ``/qps/rest/2.0/{search,get,count}/am/hostasset``
* ``/qps/rest/2.0/{search,get}/am/asset``

Docs: This QPS/AM API family is not covered by the classic VM/PC PDF; the
endpoint shapes below follow Qualys's documented QPS REST conventions (see
the API index at https://docs.qualys.com/en/vm/api/index.htm -> "Asset
Management API"). Uncertain specifics are flagged ``# TODO(verify)``.
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


def _build_search_request(
    criteria: list[tuple[str, str, str]],
    limit: int | None = None,
    offset: int | None = None,
) -> str:
    """Build a ``<ServiceRequest>`` XML body for a QPS search/count call.

    Args:
        criteria: List of ``(field, operator, value)`` tuples, ANDed by QPS.
            # TODO(verify): confirm default AND-combination semantics.
        limit: Max results per page (``preferences/limitResults``).
        offset: Pagination offset.
            # TODO(verify): confirm the exact ``preferences`` element name for
            # offset-based paging (assumed ``startFromOffset``).

    Returns:
        A ``ServiceRequest`` XML string.
    """
    parts = ["<ServiceRequest>"]
    prefs = []
    if limit is not None:
        prefs.append(f"<limitResults>{int(limit)}</limitResults>")
    if offset is not None:
        prefs.append(f"<startFromOffset>{int(offset)}</startFromOffset>")
    if prefs:
        parts.append("<preferences>" + "".join(prefs) + "</preferences>")
    if criteria:
        parts.append("<filters>")
        for field, operator, value in criteria:
            parts.append(
                f'<Criteria field="{_xml_escape(field)}" operator="{_xml_escape(operator)}">'
                f"{_xml_escape(value)}</Criteria>"
            )
        parts.append("</filters>")
    parts.append("</ServiceRequest>")
    return "".join(parts)


class HostAssetAmModule(BaseModule):
    """Read-only search/fetch over the QPS Asset Management (AM) inventory."""

    module_label = "host_asset_am"

    def register_tools(self, server: FastMCP) -> None:
        self._add_tool(server, self.search_host_assets, "search_host_assets", tier="read")
        self._add_tool(server, self.get_host_asset, "get_host_asset", tier="read")
        self._add_tool(server, self.count_host_assets, "count_host_assets", tier="read")
        self._add_tool(server, self.search_assets, "search_assets", tier="read")
        self._add_tool(server, self.get_asset, "get_asset", tier="read")

    def _host_criteria(
        self,
        name: str | None,
        ip_address: str | None,
        dns_hostname: str | None,
        netbios_name: str | None,
        os_pattern: str | None,
        tag_name: str | None,
        tag_id: int | None,
        tracking_method: str | None,
    ) -> list[tuple[str, str, str]]:
        """Build the shared hostasset filter criteria list from flat kwargs."""
        criteria: list[tuple[str, str, str]] = []
        if name is not None:
            criteria.append(("name", "CONTAINS", name))
        if ip_address is not None:
            criteria.append(("address", "EQUALS", ip_address))
        if dns_hostname is not None:
            criteria.append(("dnsHostName", "CONTAINS", dns_hostname))  # TODO(verify) field name
        if netbios_name is not None:
            criteria.append(("netbiosName", "CONTAINS", netbios_name))  # TODO(verify) field name
        if os_pattern is not None:
            criteria.append(("operatingSystem", "CONTAINS", os_pattern))  # TODO(verify) field name
        if tag_name is not None:
            criteria.append(("tagName", "EQUALS", tag_name))  # TODO(verify) field name (vs "tags.name")
        if tag_id is not None:
            criteria.append(("tagId", "EQUALS", str(tag_id)))  # TODO(verify) field name (vs "tags.id")
        if tracking_method is not None:
            criteria.append(("trackingMethod", "EQUALS", tracking_method))
        return criteria

    # ------------------------------ hostasset --------------------------- #
    def search_host_assets(
        self,
        name: str | None = None,
        ip_address: str | None = None,
        dns_hostname: str | None = None,
        netbios_name: str | None = None,
        os_pattern: str | None = None,
        tag_name: str | None = None,
        tag_id: int | None = None,
        tracking_method: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """Search the normalized host asset inventory.

        All supplied filters are ANDed together.
        # TODO(verify): confirm AND semantics and exact QPS field names for
        # the target subscription's AM API version.

        Args:
            name: Asset name substring match.
            ip_address: Exact IP address match.
            dns_hostname: DNS hostname substring match.
            netbios_name: NetBIOS name substring match.
            os_pattern: Operating system substring match.
            tag_name: Restrict to assets carrying this exact tag name.
            tag_id: Restrict to assets carrying this exact tag ID.
            tracking_method: Restrict by tracking method, e.g. "IP", "DNS",
                "NETBIOS", "AGENT", "INSTANCE_ID".
            limit: Max results per page.
            offset: Pagination offset into the result set.
                # TODO(verify): confirm preferences element name for offset paging.

        Returns:
            Parsed ServiceResponse with matching ``HostAsset`` records.
        """
        criteria = self._host_criteria(
            name, ip_address, dns_hostname, netbios_name, os_pattern, tag_name, tag_id, tracking_method
        )
        body = _build_search_request(criteria, limit=limit, offset=offset)
        return self._qps("/qps/rest/2.0/search/am/hostasset", method="POST", body_xml=body)

    def get_host_asset(self, host_asset_id: int) -> dict[str, Any]:
        """Fetch full detail for a single host asset by ID.

        Args:
            host_asset_id: The host asset ID to fetch.

        Returns:
            Parsed ServiceResponse with the ``HostAsset`` record.
        """
        return self._qps(f"/qps/rest/2.0/get/am/hostasset/{host_asset_id}", method="GET")

    def count_host_assets(
        self,
        name: str | None = None,
        ip_address: str | None = None,
        tag_name: str | None = None,
        tag_id: int | None = None,
        tracking_method: str | None = None,
    ) -> dict[str, Any]:
        """Count host assets matching the given filters (no result rows returned).

        Args:
            name: Asset name substring match.
            ip_address: Exact IP address match.
            tag_name: Restrict to assets carrying this exact tag name.
            tag_id: Restrict to assets carrying this exact tag ID.
            tracking_method: Restrict by tracking method, e.g. "IP", "DNS",
                "NETBIOS", "AGENT", "INSTANCE_ID".

        Returns:
            Parsed ServiceResponse with a ``count`` field.
        """
        criteria = self._host_criteria(
            name, ip_address, None, None, None, tag_name, tag_id, tracking_method
        )
        body = _build_search_request(criteria)
        return self._qps("/qps/rest/2.0/count/am/hostasset", method="POST", body_xml=body)

    # -------------------------- generic am/asset ------------------------ #
    def search_assets(
        self,
        name: str | None = None,
        asset_type: str | None = None,
        tag_name: str | None = None,
        tag_id: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """Search the generic normalized asset inventory (all asset types).

        Unlike :meth:`search_host_assets`, this covers the broader ``am/asset``
        resource, which can include non-host asset types depending on the
        subscription's enabled modules.
        # TODO(verify): confirm which asset types/modules populate am/asset
        # for the target subscription, and the exact ``assetType`` enum values.

        Args:
            name: Asset name substring match.
            asset_type: Restrict to a specific asset type, e.g. "HOST".
                # TODO(verify): confirm field name/enum values.
            tag_name: Restrict to assets carrying this exact tag name.
            tag_id: Restrict to assets carrying this exact tag ID.
            limit: Max results per page.
            offset: Pagination offset into the result set.

        Returns:
            Parsed ServiceResponse with matching ``Asset`` records.
        """
        criteria: list[tuple[str, str, str]] = []
        if name is not None:
            criteria.append(("name", "CONTAINS", name))
        if asset_type is not None:
            criteria.append(("type", "EQUALS", asset_type))  # TODO(verify) field name
        if tag_name is not None:
            criteria.append(("tagName", "EQUALS", tag_name))  # TODO(verify) field name
        if tag_id is not None:
            criteria.append(("tagId", "EQUALS", str(tag_id)))  # TODO(verify) field name
        body = _build_search_request(criteria, limit=limit, offset=offset)
        return self._qps("/qps/rest/2.0/search/am/asset", method="POST", body_xml=body)

    def get_asset(self, asset_id: int) -> dict[str, Any]:
        """Fetch full detail for a single normalized asset by ID.

        Args:
            asset_id: The AM asset ID to fetch.

        Returns:
            Parsed ServiceResponse with the ``Asset`` record.
        """
        return self._qps(f"/qps/rest/2.0/get/am/asset/{asset_id}", method="GET")
