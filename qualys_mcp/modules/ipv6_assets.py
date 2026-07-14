"""IPv6 Assets module (classic FO API) — IPv4<->IPv6 mapping records.

Covers:
* IPv6 Mapping Record List (``/api/2.0/fo/asset/ip/v4_v6`` action=list).
* Add IPv6 Mapping Records (``/api/2.0/fo/asset/ip/v4_v6`` action=add).

Requires the IPv6 Support feature to be enabled for the subscription (Qualys
Support must enable it). Each mapping record associates one IPv6 address with
one special IPv4 address in the reserved 0.0.0.1-0.254.255.255 range, which is
what scans and reports actually target; the true IPv6 address is then shown
alongside detections in the Host List Detection API output.

Docs: Qualys VM/PC API User Guide — "IPv6 Assets" chapter.
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class Ipv6AssetsModule(BaseModule):
    """List and add IPv4<->IPv6 mapping records for IPv6 asset management."""

    module_label = "ipv6_assets"

    def register_tools(self, server: FastMCP) -> None:
        self._add_tool(
            server, self.list_ipv6_mapping_records, "list_ipv6_mapping_records", tier="read"
        )
        self._add_tool(
            server, self.add_ipv6_mapping_records, "add_ipv6_mapping_records", tier="write"
        )

    def list_ipv6_mapping_records(
        self,
        id_min: int | None = None,
        id_max: int | None = None,
        ipv4_filter: str | None = None,
        ipv6_network: str | None = None,
        output_format: str = "csv",
        truncation_limit: int | None = None,
        echo_request: bool | None = None,
    ) -> dict[str, Any]:
        """List IPv6 mapping records in the subscription.

        Args:
            id_min: Minimum mapping record ID (inclusive).
            id_max: Maximum mapping record ID (inclusive).
            ipv4_filter: Restrict to mapping records with this IPv4 address.
            ipv6_network: Restrict to mapping records within this IPv6 network address.
            output_format: "csv" (default per the Qualys API) or "xml". Qualys
                only accepts lowercase.
            truncation_limit: Max records to return (1-1000000; default 5000 when
                unspecified).
            echo_request: Echo input parameters back in the output.

        Returns:
            Parsed IP_MAP_LIST_OUTPUT for "xml", or ``{"raw": ...}`` for csv.
            Truncated results include a <WARNING> with instructions for the
            next batch.
        """
        params = {
            "action": "list",
            "id_min": id_min,
            "id_max": id_max,
            "ipv4_filter": ipv4_filter,
            "ipv6_network": ipv6_network,
            "output_format": output_format.lower(),
            "truncation_limit": truncation_limit,
            "echo_request": echo_request,
        }
        parse = output_format.lower() == "xml"
        return self._fo(
            "/api/2.0/fo/asset/ip/v4_v6", method="GET", params=params, parse=parse
        )

    def add_ipv6_mapping_records(
        self,
        csv_data: str | None = None,
        xml_data: str | None = None,
        all_or_nothing: bool | None = None,
        echo_request: bool | None = None,
    ) -> dict[str, Any]:
        """Add IPv6 mapping records to the subscription.

        Each record associates one IPv6 address with one special IPv4 address
        in the reserved 0.0.0.1-0.254.255.255 range. A maximum of 10,000
        records can be added per request. Exactly one of ``csv_data`` or
        ``xml_data`` must be provided.

        Args:
            csv_data: CSV-formatted mapping data with columns IPv4, IPv6, and an
                optional custom ID (see the Qualys "How to Add IPv6 Records in
                CSV" guide for exact formatting). Mutually exclusive with xml_data.
            xml_data: An ``<IP_MAP_LIST>`` XML document containing one or more
                ``<IP_MAP><V4>...</V4><V6>...</V6></IP_MAP>`` entries. Mutually
                exclusive with csv_data.
            all_or_nothing: When True (default) the whole request is rejected if
                any record has an IP conflict. When False, conflicting records
                are skipped but non-conflicting records are still added.
            echo_request: Echo input parameters back in the output.

        Returns:
            SIMPLE_RETURN confirming how many records were imported, or an
            error dict.
        """
        if not csv_data and not xml_data:
            return {"error": "One of csv_data or xml_data is required."}
        if csv_data and xml_data:
            return {"error": "csv_data and xml_data cannot both be specified."}
        data = {
            "action": "add",
            "csv_data": csv_data,
            "xml_data": xml_data,
            "all_or_nothing": all_or_nothing,
            "echo_request": echo_request,
        }
        return self._fo("/api/2.0/fo/asset/ip/v4_v6", method="POST", data=data)
