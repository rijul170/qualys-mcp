"""KnowledgeBase module (classic FO API) — REFERENCE read-only module.

Demonstrates the read-only pattern that builder agents should copy:
* subclass BaseModule, set ``module_label``
* one method per tool, fully type-hinted with a clear docstring
* register with tier="read"
* call ``self._fo(...)`` and return the parsed dict

Endpoint: ``/api/2.0/fo/knowledge_base/vuln/`` (action=list).
Docs: Qualys VM/PC API User Guide — "KnowledgeBase".
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class KnowledgeBaseModule(BaseModule):
    """Query the Qualys vulnerability KnowledgeBase (QIDs)."""

    module_label = "knowledgebase"

    def register_tools(self, server: FastMCP) -> None:
        self._add_tool(server, self.list_knowledgebase, "list_knowledgebase", tier="read")
        self._add_tool(server, self.get_qids, "get_qids", tier="read")
        self._add_tool(server, self.reset_vulnerability, "reset_vulnerability", tier="write")
        self._add_tool(server, self.download_qvs_json, "download_qvs_json", tier="read")
        self._add_tool(server, self.list_vendor_references, "list_vendor_references", tier="read")
        self._add_tool(server, self.edit_vulnerability, "edit_vulnerability", tier="write")

    def list_knowledgebase(
        self,
        details: str = "Basic",
        ids: str | None = None,
        id_min: int | None = None,
        id_max: int | None = None,
        last_modified_after: str | None = None,
        last_modified_before: str | None = None,
        is_patchable: bool | None = None,
    ) -> dict[str, Any]:
        """List vulnerabilities (QIDs) from the Qualys KnowledgeBase.

        CVE, CVSS, and PCI data are returned automatically based on ``details``
        ("All" includes the full CVE_LIST, CVSS scores, and PCI flags). The
        classic KB ``list`` action has no show_cve/show_cvss/show_pci_reasons
        toggles — passing them is rejected by the API.

        Args:
            details: Level of detail — "Basic", "All", or "None". Use "All" to
                include CVE references, CVSS scores, and PCI reasons.
            ids: Comma-separated QIDs to fetch (e.g. "38170,38173").
            id_min: Lower bound QID for a range query.
            id_max: Upper bound QID for a range query.
            last_modified_after: ISO date (YYYY-MM-DD) — only QIDs modified after.
            last_modified_before: ISO date (YYYY-MM-DD) — only QIDs modified before.
            is_patchable: Restrict to patchable (True) / non-patchable (False) QIDs.

        Returns:
            Parsed KnowledgeBase response (KNOWLEDGE_BASE_VULN_LIST_OUTPUT).
        """
        params = {
            "action": "list",
            "details": details,
            "ids": ids,
            "id_min": id_min,
            "id_max": id_max,
            "last_modified_after": last_modified_after,
            "last_modified_before": last_modified_before,
            "is_patchable": is_patchable,
        }
        return self._fo("/api/2.0/fo/knowledge_base/vuln/", method="GET", params=params)

    def get_qids(self, ids: str, details: str = "All") -> dict[str, Any]:
        """Fetch full detail for specific QIDs.

        Args:
            ids: Comma-separated QIDs (e.g. "38170,90783").
            details: "Basic" or "All" (default "All" for full detail).

        Returns:
            Parsed KnowledgeBase response for the requested QIDs.
        """
        params = {"action": "list", "ids": ids, "details": details}
        return self._fo("/api/2.0/fo/knowledge_base/vuln/", method="GET", params=params)

    def reset_vulnerability(self, qid: int) -> dict[str, Any]:
        """Reset a customized vulnerability back to its Qualys defaults.

        Reverts any user customizations made to the QID (custom severity,
        disabled flag, and appended Threat/Impact/Solution comments) so the
        vulnerability returns to the service-provided settings. Manager role
        required.

        Args:
            qid: The QID of the vulnerability to reset (e.g. 27014).

        Returns:
            SIMPLE_RETURN confirming the reset ("Custom Vuln Data has been
            reset successfully"), or an error dict.
        """
        data = {"action": "reset", "qid": qid}
        return self._fo("/api/2.0/fo/knowledge_base/vuln/", method="POST", data=data)

    def download_qvs_json(
        self,
        cve: str,
        details: str = "Basic",
        qvs_last_modified_before: str | None = None,
        qvs_last_modified_after: str | None = None,
        qvs_min: int | None = None,
        qvs_max: int | None = None,
        nvd_published_before: str | None = None,
        nvd_published_after: str | None = None,
    ) -> dict[str, Any]:
        """Download Qualys Vulnerability Score (QVS) data from the KnowledgeBase.

        The QVS is a Qualys-assigned score (0-100) derived from CVSS, EPSS,
        active-exploitation and other threat-intel signals. This endpoint
        returns JSON (not XML) via ``/api/2.0/fo/knowledge_base/qvs/``.

        Confirmed via
        https://docs.qualys.com/en/vm/api/scans/kbase/knowledgebase_qvs.htm:
        ``cve`` is a required parameter (along with ``action`` and
        ``details``, both already always sent) — the live audit's HTTP 400
        was this endpoint being called with no CVE filter at all. Callers
        must supply at least one CVE ID.

        Args:
            cve: Comma-separated CVE IDs to filter on (e.g.
                "CVE-2021-36764,CVE-2017-0199"). Required by the API.
            details: "Basic" to show only the base QVS, or "All" to include
                contributing factors (cvss, epss, exploitMaturity,
                threatActors, malwareName, trending, cisaVuln, etc).
            qvs_last_modified_before: ISO date/datetime
                (YYYY-MM-DD[THH:MM:SSZ]) — only CVEs whose QVS was last
                modified before this timestamp.
            qvs_last_modified_after: ISO date/datetime — only CVEs whose QVS
                was last modified after this timestamp.
            qvs_min: Minimum QVS value (inclusive) to include.
            qvs_max: Maximum QVS value (inclusive) to include.
            nvd_published_before: ISO date/datetime — only CVEs NVD-published
                before this timestamp.
            nvd_published_after: ISO date/datetime — only CVEs NVD-published
                after this timestamp.

        Returns:
            The endpoint responds with JSON (not XML); since ``self._fo``
            normalizes XML by default, this call passes ``parse=False`` and
            returns ``{"raw": "<json text>"}`` — the caller should parse the
            "raw" value as JSON.
        """
        params = {
            "action": "list",
            "details": details,
            "cve": cve,
            "qvs_last_modified_before": qvs_last_modified_before,
            "qvs_last_modified_after": qvs_last_modified_after,
            "qvs_min": qvs_min,
            "qvs_max": qvs_max,
            "nvd_published_before": nvd_published_before,
            "nvd_published_after": nvd_published_after,
        }
        return self._fo(
            "/api/2.0/fo/knowledge_base/qvs/", method="GET", params=params, parse=False
        )

    def list_vendor_references(self, qids: str | None = None) -> dict[str, Any]:
        """List vendor references (patches/advisories) for QIDs in the KnowledgeBase.

        Args:
            qids: Comma-separated QIDs to restrict output to those vendor
                references only. When omitted, all vendor references are
                returned.

        Returns:
            Parsed VENDOR_REFERENCE_LIST_OUTPUT (vendor reference + URL per QID).
        """
        params = {"action": "list_vendor_references", "qids": qids}
        return self._fo("/api/2.0/fo/vendor/", method="GET", params=params)

    def edit_vulnerability(
        self,
        qid: int,
        severity: int | None = None,
        disable: bool | None = None,
        threat_comment: str | None = None,
        impact_comment: str | None = None,
        solution_comment: str | None = None,
    ) -> dict[str, Any]:
        """Edit a vulnerability's severity, disabled state, or comments.

        Providing at least one optional parameter is required by the API.
        Comments are appended to the service-provided Threat/Impact/Solution
        descriptions in the vulnerability details. Use ``reset_vulnerability``
        to revert a QID to its original KnowledgeBase settings.

        Args:
            qid: QID of the vulnerability to edit.
            severity: New severity level, 1-5. Changes how the vulnerability
                is prioritized/reported.
            disable: True to globally disable the vulnerability (filtered out
                of all hosts, scan reports, host info, asset search, and
                dashboards); False to leave it enabled.
            threat_comment: Plain-text comment appended to the Threat section.
            impact_comment: Plain-text comment appended to the Impact section.
            solution_comment: Plain-text comment appended to the Solution
                section.

        Returns:
            SIMPLE_RETURN status ("Custom Vuln Data has been updated
            successfully"), or an error dict.
        """
        data = {
            "action": "edit",
            "qid": qid,
            "severity": severity,
            "disable": disable,
            "threat_comment": threat_comment,
            "impact_comment": impact_comment,
            "solution_comment": solution_comment,
        }
        return self._fo("/api/2.0/fo/knowledge_base/vuln/", method="POST", data=data)
