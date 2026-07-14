"""Policy Compliance — SCAP module (classic FO API).

Covers SCAP policy listing plus the two SCAP compliance report formats:
Cyberscope (FISMA reporting, LASR XML format) and ARF (Asset Reporting
Format, SCAP 1.2 / NIST requirement).

Docs: Qualys VM/PC API User Guide — "SCAP Cyberscope Report", "SCAP ARF
Report", "SCAP Policy List".
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class ScapModule(BaseModule):
    """List SCAP policies and generate SCAP compliance reports."""

    module_label = "scap"

    def register_tools(self, server: FastMCP) -> None:
        self._add_tool(server, self.list_scap_policies, "list_scap_policies", tier="read")
        self._add_tool(server, self.get_cyberscope_report, "get_cyberscope_report", tier="read")
        self._add_tool(server, self.get_scap_arf_report, "get_scap_arf_report", tier="read")

    def list_scap_policies(
        self,
        details: str = "Basic",
        ids: str | None = None,
        id_min: int | None = None,
        id_max: int | None = None,
        echo_request: bool | None = None,
    ) -> dict[str, Any]:
        """List SCAP (FDCC) policies visible to the user.

        Args:
            details: "None" (ID and title only), "Basic" (default; all SCAP
                policy details except asset group list and SCAP file list),
                or "All" (all SCAP policy details).
            ids: Comma-separated SCAP policy IDs and/or ID ranges (e.g.
                "190-400").
            id_min: Lower bound SCAP policy ID for a range query.
            id_max: Upper bound SCAP policy ID for a range query.
            echo_request: Echo the request's input parameters in the output.

        Returns:
            Parsed FDCC_POLICY_LIST_OUTPUT.
        """
        params = {
            "action": "list",
            "details": details,
            "ids": ids,
            "id_min": id_min,
            "id_max": id_max,
            "echo_request": echo_request,
        }
        return self._fo("/api/2.0/fo/compliance/fdcc_policy/", method="GET", params=params)

    def get_cyberscope_report(
        self,
        report_type: str = "scan",
        scan_id: str | None = None,
        scan_ref: str | None = None,
        policy_id: str | None = None,
        ips: str | None = None,
        ag_ids: str | None = None,
        organisation_name1: str | None = None,
        organisation_name2: str | None = None,
        organisation_name3: str | None = None,
    ) -> dict[str, Any]:
        """Generate a Cyberscope-compatible XML report (LASR format) for FISMA reporting.

        Args:
            report_type: Which Cyberscope report to build:
                "scan" (single SCAP scan's raw results; requires ``scan_id``
                or ``scan_ref``), "policy" (saved SCAP scan data for one SCAP
                policy; requires ``policy_id``), or "global" (SCAP data for
                all SCAP policies plus automatic VM scan data; requires
                ``ips`` and/or ``ag_ids``).
            scan_id: SCAP scan ID (report_type "scan"; required unless
                ``scan_ref`` given). Found in the SCAP scan results URL in
                the Qualys UI.
            scan_ref: SCAP scan reference number, e.g.
                "qscap/1337984725.4360" (report_type "scan"; alternative to
                ``scan_id``).
            policy_id: SCAP policy ID (report_type "policy"; required).
                Found in the SCAP policy editor URL in the Qualys UI.
            ips: Comma-separated IPs/ranges to restrict included hosts to
                (report_type "scan"/"policy"/"global"; required for "global"
                unless ``ag_ids`` given).
            ag_ids: Comma-separated asset group IDs to restrict included
                hosts to (report_type "policy"/"global"; required for
                "global" unless ``ips`` given).
            organisation_name1: Value for the report's first
                ``<ai:Organization>`` element.
            organisation_name2: Value for the second organization element.
            organisation_name3: Value for the third organization element.

        Returns:
            Parsed Cyberscope XML report (LASR format), or an error dict.
        """
        report_type = report_type.lower().strip()
        path_map = {
            "scan": "/api/2.0/fo/asset/host/cyberscope/fdcc/scan/",
            "policy": "/api/2.0/fo/asset/host/cyberscope/fdcc/policy/",
            "global": "/api/2.0/fo/asset/host/cyberscope/",
        }
        if report_type not in path_map:
            return {"error": "report_type must be one of: scan, policy, global"}
        params = {
            "scan_id": scan_id,
            "scan_ref": scan_ref,
            "policy_id": policy_id,
            "ips": ips,
            "ag_ids": ag_ids,
            "organisation_name1": organisation_name1,
            "organisation_name2": organisation_name2,
            "organisation_name3": organisation_name3,
        }
        return self._fo(path_map[report_type], method="GET", params=params)

    def get_scap_arf_report(
        self,
        scan_id: str,
        ips: str | None = None,
        ips_network_id: int | None = None,
    ) -> dict[str, Any]:
        """Generate a SCAP scan report in Asset Reporting Format (ARF 1.1 Schema).

        Args:
            scan_id: Scan ID for a finished SCAP scan. Found in the SCAP scan
                results URL in the Qualys UI.
            ips: Comma-separated IPs/ranges to restrict the report to.
            ips_network_id: Network ID to restrict the report's target IPs
                to. Only valid when Network Support is enabled, the policy
                has SCAP 1.2 content, and ``ips`` is also specified.

        Returns:
            Parsed ARF 1.1-compliant XML report.
        """
        params = {
            "scan_id": scan_id,
            "ips": ips,
            "ips_network_id": ips_network_id,
        }
        return self._fo("/api/2.0/fo/compliance/scap/arf/", method="GET", params=params)
