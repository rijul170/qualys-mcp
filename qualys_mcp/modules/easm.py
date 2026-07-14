"""EASM module (Gateway/JWT API) — External Attack Surface Management.

External Attack Surface Management is delivered as part of Qualys
CyberSecurity Asset Management (CSAM) 2.0+. It provides an outside-in view of
internet-facing assets (domains, subdomains, IPs, cloud workloads, web apps,
certificates) discovered from external signals, plus the risks/findings on
that attack surface.

Gateway host + Bearer-JWT auth (fetched automatically by the client). Paths
below are the CSAM gateway asset endpoints (``/rest/2.0/...``) and the EASM
configuration endpoints (``/easm/v1/...``).

Docs: https://docs.qualys.com/en/csam/latest/inventory/sensors/easm.htm and
the CSAM API guide. This is a newer Gateway product and the exact
search-body/discovery/seed shapes are not fully pinned down here — every
uncertain path/param/body is flagged ``# TODO(verify)``.
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class EasmModule(BaseModule):
    """List/search external assets and attack surface findings; drive discovery."""

    module_label = "easm"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(server, self.list_external_assets, "list_external_assets", tier="read")
        self._add_tool(server, self.get_external_asset, "get_external_asset", tier="read")
        self._add_tool(
            server,
            self.list_attack_surface_findings,
            "list_attack_surface_findings",
            tier="read",
        )
        # Writes
        self._add_tool(server, self.trigger_easm_discovery, "trigger_easm_discovery", tier="write")
        self._add_tool(server, self.add_easm_seed, "add_easm_seed", tier="write")

    # ------------------------------ reads ------------------------------ #
    def list_external_assets(
        self,
        filter_ql: str | None = None,
        page_number: int = 0,
        page_size: int = 50,
        include_easm_only: bool = True,
    ) -> dict[str, Any]:
        """Search external (internet-facing) assets in the CSAM/EASM inventory.

        Args:
            filter_ql: Qualys Query Language (QQL) filter string, e.g.
                ``"asset.name: example.com"`` or a source/tag expression.
                # TODO(verify): confirm the request-body field name for the
                # filter — CSAM gateway search has used both ``filter`` and
                # ``filterQL``/``filterRequest`` across versions.
            page_number: Zero-based page index.
            page_size: Records per page (max is version-dependent, ~300).
                # TODO(verify): confirm max page size.
            include_easm_only: When True, restrict to assets whose source is
                External Attack Surface (vs. all CSAM-inventoried assets).
                # TODO(verify): confirm the source filter value/field used to
                # scope to EASM-discovered assets (e.g. ``source: EASM``).

        Returns:
            Parsed gateway JSON with the matching external asset records.
        """
        body: dict[str, Any] = {
            "pageNumber": page_number,
            "pageSize": page_size,
        }
        if filter_ql is not None:
            body["filter"] = filter_ql  # TODO(verify) body field name
        if include_easm_only:
            # TODO(verify): correct field/value to scope results to EASM source.
            body["source"] = "EASM"
        # TODO(verify): confirm CSAM gateway asset-search path and method.
        return self._gateway("/rest/2.0/search/am/asset", method="POST", json=body)

    def get_external_asset(self, asset_id: int) -> dict[str, Any]:
        """Fetch full detail for a single external/CSAM asset by ID.

        Args:
            asset_id: The CSAM asset ID to fetch.

        Returns:
            Parsed gateway JSON with the asset record.
        """
        # TODO(verify): confirm get-by-id path — assumed ``/rest/2.0/get/am/asset/{id}``.
        return self._gateway(f"/rest/2.0/get/am/asset/{asset_id}", method="GET")

    def list_attack_surface_findings(
        self,
        field: str | None = None,
        value: str | None = None,
        operator: str = "EQUALS",
        last_seen_id: int | None = None,
    ) -> dict[str, Any]:
        """List external attack surface findings (vulnerabilities discovered by EASM scans).

        Path/body confirmed via the CSAM API guide's "GET List of
        Vulnerabilities discovered by EASM Scan"
        (https://docs.qualys.com/en/csam/api/vulnerabilities/vulns_discovered_easm_scan.htm):
        ``POST /rest/2.0/search/am/easm/scan/vulns``, filter body shaped as
        ``{"filters": [{"field": ..., "operator": ..., "value": ...}]}``
        (the older ``/easm/v1/findings/search`` guess 404s — no such
        resource exists). Response envelope matches the other ``am/*``
        gateway searches in this codebase (``responseCode``, ``count``,
        ``lastSeenId``/``lastSeenAssetId``, ``hasMore``).

        Args:
            field: Attribute to filter on, e.g. "vulnerabilities.severity",
                "vulnerabilities.qid", "vulnerabilities.status",
                "asset.assetId", "vulnerabilities.found",
                "vulnerabilities.ignored", "vulnerabilities.disabled".
            value: The comparison value for ``field``.
            operator: Comparison operator, e.g. "EQUALS". Defaults to "EQUALS".
            last_seen_id: Pagination cursor — pass the previous page's
                ``lastSeenId`` to fetch the next page.

        Returns:
            Parsed gateway JSON with ``easmVulnerabilityListData.vulnerabilities``
            plus ``count``/``lastSeenId``/``hasMore`` paging metadata.
        """
        body: dict[str, Any] = {}
        if field is not None and value is not None:
            body["filters"] = [{"field": field, "operator": operator, "value": str(value)}]
        params = {"lastSeenId": last_seen_id}
        return self._gateway(
            "/rest/2.0/search/am/easm/scan/vulns", method="POST", params=params, json=body or None
        )

    # ------------------------------ writes ----------------------------- #
    def trigger_easm_discovery(self, profile_id: int) -> dict[str, Any]:
        """Trigger an on-demand EASM discovery run for a profile.

        Args:
            profile_id: The EASM profile ID to run discovery for.

        Returns:
            Parsed gateway JSON confirming the discovery request.
        """
        # TODO(verify): confirm the discovery-trigger path/method/body. Assumed
        # a POST to a profile sub-resource; may instead be
        # ``/easm/v1/profile/{id}/discover`` or require a body describing scope.
        return self._gateway(
            f"/easm/v1/profile/{profile_id}/discovery", method="POST", json={}
        )

    def add_easm_seed(
        self,
        profile_id: int,
        seed_value: str,
        seed_type: str = "DOMAIN",
    ) -> dict[str, Any]:
        """Add a seed (domain/subdomain/IP) to an EASM profile's discovery scope.

        Args:
            profile_id: The EASM profile ID to add the seed to.
            seed_value: The seed value, e.g. "example.com" or "sub.example.com".
            seed_type: Seed kind — "DOMAIN", "SUBDOMAIN", or "IP".
                # TODO(verify): confirm the accepted seed-type enum values.

        Returns:
            Parsed gateway JSON confirming the seed was added.
        """
        # TODO(verify): confirm path and body field names for adding seeds.
        # Assumed the EASM profile exposes a seeds sub-resource that accepts a
        # {type, value} object.
        body = {"type": seed_type, "value": seed_value}
        return self._gateway(
            f"/easm/v1/profile/{profile_id}/seeds", method="POST", json=body
        )
