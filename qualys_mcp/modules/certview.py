"""CertView module (Gateway/JWT API) — Certificate inventory & assessment.

Search and inspect the TLS/SSL certificate inventory Qualys CertView builds
from scans and Cloud Agents: certificate search with rich filters, per-cert
detail, certificate/host instances, and certificate authorities.

Gateway host + Bearer-JWT auth (fetched automatically by the client). The
list/search endpoint is ``POST /certview/v2/certificates`` with a JSON filter
body; this is confirmed from the CertView API guide. The per-certificate,
instances, CA, and count sub-resources are less firmly documented and are
flagged ``# TODO(verify)``.

Docs: https://docs.qualys.com/en/certview/api/certview_api/ch02/list_certificates_v2.htm
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class CertviewModule(BaseModule):
    """Read-only search and inspection of the CertView certificate inventory."""

    module_label = "certview"

    def register_tools(self, server: FastMCP) -> None:
        self._add_tool(server, self.search_certificates, "search_certificates", tier="read")
        self._add_tool(server, self.get_certificate, "get_certificate", tier="read")
        self._add_tool(
            server, self.list_certificate_instances, "list_certificate_instances", tier="read"
        )
        self._add_tool(
            server, self.list_certificate_authorities, "list_certificate_authorities", tier="read"
        )
        self._add_tool(server, self.count_certificates, "count_certificates", tier="read")

    @staticmethod
    def _filter_body(
        field: str | None,
        value: str | None,
        operator: str,
        page_number: int,
        page_size: int,
        includes: str | None,
    ) -> dict[str, Any]:
        """Build the CertView v2 search request body from flat kwargs.

        Args:
            field: Certificate/asset attribute to filter on (e.g.
                ``certificate.serialNumber``, ``certificate.hash``,
                ``asset.primaryIp``, ``certificate.validToDate``).
            value: The comparison value.
            operator: One of "EQUALS", "CONTAINS", "IN", "GREATER", "LESSER".
            page_number: Zero-based page index.
            page_size: Records per page (max 200).
            includes: Comma-separated optional facets to include, e.g.
                "VULNERABILITIES,CIPHER_SUITES,ASSET_TAGS".

        Returns:
            The JSON body dict for ``POST /certview/v2/certificates``.
        """
        body: dict[str, Any] = {"pageNumber": page_number, "pageSize": page_size}
        if field is not None and value is not None:
            body["filter"] = {
                "filters": [{"field": field, "value": value, "operator": operator}],
                "operation": "AND",
            }
        if includes is not None:
            body["includes"] = [tok.strip() for tok in includes.split(",") if tok.strip()]
        return body

    def search_certificates(
        self,
        field: str | None = None,
        value: str | None = None,
        operator: str = "EQUALS",
        page_number: int = 0,
        page_size: int = 50,
        includes: str | None = None,
    ) -> dict[str, Any]:
        """Search the certificate inventory (v2 — no fixed result cap).

        Args:
            field: Attribute to filter on, e.g. "certificate.serialNumber",
                "certificate.subject.cn", "certificate.validToDate",
                "asset.primaryIp".
            value: The comparison value for ``field``.
            operator: Comparison operator — "EQUALS", "CONTAINS", "IN",
                "GREATER", "LESSER". Defaults to "EQUALS".
            page_number: Zero-based page index.
            page_size: Records per page (default 50, max 200).
            includes: Comma-separated optional facets, e.g.
                "VULNERABILITIES,CIPHER_SUITES,ASSET_TAGS".

        Returns:
            Parsed gateway JSON with matching certificates (subject/issuer,
            key algorithm & size, validity, grade, associated hosts).
        """
        body = self._filter_body(field, value, operator, page_number, page_size, includes)
        return self._gateway("/certview/v2/certificates", method="POST", json=body)

    def get_certificate(self, certificate_id: str) -> dict[str, Any]:
        """Fetch full detail for a single certificate by its CertView ID/hash.

        Args:
            certificate_id: The CertView certificate ID (or certificate hash).

        Returns:
            Parsed gateway JSON with the certificate record.
        """
        # TODO(verify): CertView v2 documents only the unified POST-search
        # endpoint; there may be no dedicated GET-by-id. This assumes a
        # ``/certview/v2/certificates/{id}`` GET exists — if not, callers
        # should use search_certificates(field="certificate.hash", ...).
        return self._gateway(f"/certview/v2/certificates/{certificate_id}", method="GET")

    def list_certificate_instances(
        self,
        certificate_id: str | None = None,
        page_number: int = 0,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """List certificate/server instances (where certificates are deployed).

        Args:
            certificate_id: Restrict instances to this certificate ID/hash.
            page_number: Zero-based page index.
            page_size: Records per page.

        Returns:
            Parsed gateway JSON with server/certificate instance records
            (host, port, protocol, grade per deployment).
        """
        # TODO(verify): confirm the instances endpoint path/body. The CertView
        # docs reference a "List Server Instances" API; path assumed here as
        # ``/certview/v2/instances``.
        body: dict[str, Any] = {"pageNumber": page_number, "pageSize": page_size}
        if certificate_id is not None:
            body["filter"] = {
                "filters": [
                    {"field": "certificate.id", "value": certificate_id, "operator": "EQUALS"}
                ],
                "operation": "AND",
            }  # TODO(verify) filter field name
        return self._gateway("/certview/v2/instances", method="POST", json=body)

    def list_certificate_authorities(
        self,
        page_number: int = 0,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """List certificate authorities (issuers) seen across the inventory.

        Args:
            page_number: Zero-based page index.
            page_size: Records per page.

        Returns:
            Parsed gateway JSON with CA/issuer records and their counts.
        """
        # TODO(verify): live audit observed 404 NOT_FOUND "No static resource
        # certview/v2/cas." on this path. Reviewed the full CertView API guide
        # chapter 2 (Certificate API) at
        # https://docs.qualys.com/en/certview/api/certview_api/ch02/certificateapi.htm
        # — it documents exactly four endpoints (List Certificates v1/v2,
        # List Assets for a Certificate, List Server Instances) and NONE of
        # them is a certificate-authorities listing. Certificate Authorities
        # only appear as a UI feature (Configuration > Approved CAs,
        # https://docs.qualys.com/en/certview/latest/certificates/certificate_authorities.htm)
        # with no documented REST endpoint found. Best hypothesis: CA/issuer
        # data must be derived client-side from
        # ``search_certificates(field="certificate.issuer...", ...)`` facets
        # rather than a dedicated CA resource. Left unchanged pending a
        # confirmed path — do not guess further without live console access.
        body = {"pageNumber": page_number, "pageSize": page_size}
        return self._gateway("/certview/v2/cas", method="POST", json=body)

    def count_certificates(
        self,
        field: str | None = None,
        value: str | None = None,
        operator: str = "EQUALS",
    ) -> dict[str, Any]:
        """Count certificates matching a filter (no certificate rows returned).

        Args:
            field: Attribute to filter on (see :meth:`search_certificates`).
            value: The comparison value for ``field``.
            operator: Comparison operator — "EQUALS", "CONTAINS", "IN".

        Returns:
            Parsed gateway JSON with a certificate count.
        """
        # TODO(verify): live audit observed 404 NOT_FOUND "No static resource
        # certview/v2/certificates/count." on this path. Reviewed the CertView
        # API guide chapter 2 index
        # (https://docs.qualys.com/en/certview/api/certview_api/ch02/certificateapi.htm)
        # and the List Certificates v2 response docs — no dedicated count
        # endpoint is documented, and the search response body itself does not
        # appear to carry a total-count/hasMore field either (unlike the
        # GAV/CSAM/EASM ``am/asset``-family responses). Best hypothesis: there
        # is no separate count resource for CertView v2; callers must page
        # through ``search_certificates`` and count rows client-side. Left
        # unchanged pending a confirmed path.
        body: dict[str, Any] = {}
        if field is not None and value is not None:
            body["filter"] = {
                "filters": [{"field": field, "value": value, "operator": operator}],
                "operation": "AND",
            }
        return self._gateway("/certview/v2/certificates/count", method="POST", json=body)
