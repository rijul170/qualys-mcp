"""WAS Reports module (QPS REST 3.0 API).

Web Application Scanning (WAS) is not covered by the classic VM/PC API guide;
it lives entirely under the QPS REST 3.0 family at ``/qps/rest/3.0/.../was/report``.
Endpoint shapes below are built from the public WAS API reference
(https://docs.qualys.com/en/was/api/report_creation/) — uncertain nested fields
are flagged with ``# TODO(verify)``.

Docs: Qualys WAS API User Guide — "Report Creation".
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class WasReportsModule(BaseModule):
    """Search, generate, download, and delete WAS reports."""

    module_label = "was_reports"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(server, self.search_was_reports, "search_was_reports", tier="read")
        self._add_tool(server, self.download_was_report, "download_was_report", tier="read")
        # Writes
        self._add_tool(server, self.create_was_report, "create_was_report", tier="write")
        # Destructive
        self._add_tool(server, self.delete_was_report, "delete_was_report", tier="destructive")

    # ------------------------------------------------------------------ #
    # XML helpers (duplicated per-module by design; see MODULE_BUILD_GUIDE.md).
    # ------------------------------------------------------------------ #
    @staticmethod
    def _esc(value: Any) -> str:
        """Escape a scalar value for use as XML character data."""
        text = "true" if value is True else "false" if value is False else str(value)
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    @classmethod
    def _field(cls, tag: str, value: Any) -> str:
        """Render one non-null XML element (supports one level of dict nesting)."""
        if value is None:
            return ""
        if isinstance(value, dict):
            inner = "".join(cls._field(k, v) for k, v in value.items())
            return f"<{tag}>{inner}</{tag}>"
        return f"<{tag}>{cls._esc(value)}</{tag}>"

    @classmethod
    def _criteria(cls, field: str, operator: str, value: Any) -> str:
        """Render a ``<Criteria>`` filter element, or '' if value is None."""
        if value is None:
            return ""
        return f'<Criteria field="{field}" operator="{operator}">{cls._esc(value)}</Criteria>'

    def _search_body(self, *criteria: str, limit: int | None = None, offset: int | None = None) -> str:
        """Build a ``<ServiceRequest>`` body with optional filters + paging preferences.

        # TODO(verify): preference element names follow the common QPS 3.0
        # convention (``limitResults``/``startFromOffset``) but are not confirmed
        # against the WAS API guide excerpt available at build time.
        """
        filters = "".join(c for c in criteria if c)
        prefs_inner = self._field("limitResults", limit) + self._field("startFromOffset", offset)
        prefs = f"<preferences>{prefs_inner}</preferences>" if prefs_inner else ""
        filters_block = f"<filters>{filters}</filters>" if filters else ""
        return f"<ServiceRequest>{prefs}{filters_block}</ServiceRequest>"

    def _data_body(self, entity_tag: str, fields: str) -> str:
        """Build a ``<ServiceRequest><data><Tag>...</Tag></data></ServiceRequest>`` body."""
        return f"<ServiceRequest><data><{entity_tag}>{fields}</{entity_tag}></data></ServiceRequest>"

    # ------------------------------------------------------------------ #
    # Reads
    # ------------------------------------------------------------------ #
    def search_was_reports(
        self,
        report_id: int | None = None,
        name_contains: str | None = None,
        report_type: str | None = None,
        status: str | None = None,
        created_after: str | None = None,
        limit: int = 20,
        offset: int = 1,
    ) -> dict[str, Any]:
        """Search generated/in-progress WAS reports.

        Args:
            report_id: Restrict to a single report ID (``id``, EQUALS).
            name_contains: Substring match on report name (``name``, CONTAINS).
            report_type: "WAS_WEBAPP_REPORT", "WAS_SCAN_REPORT", or
                "WAS_COMPARISON_REPORT" (``type``, EQUALS).
            status: Report generation status.
                # TODO(verify): exact enum values (e.g. "SUBMITTED", "RUNNING",
                # "FINISHED", "ERROR") for the report ``status`` field.
            created_after: ISO datetime lower bound for ``createdDate``
                (``YYYY-MM-DDTHH:MM:SSZ``).
            limit: Max results per page (preference ``limitResults``).
            offset: 1-based starting offset (preference ``startFromOffset``).

        Returns:
            Parsed ``ServiceResponse`` containing a list of ``Report`` records.
        """
        criteria = [
            self._criteria("id", "EQUALS", report_id),
            self._criteria("name", "CONTAINS", name_contains),
            self._criteria("type", "EQUALS", report_type),
            self._criteria("status", "EQUALS", status),  # TODO(verify): status enum
            self._criteria("createdDate", "GREATER", created_after),
        ]
        body = self._search_body(*criteria, limit=limit, offset=offset)
        return self._qps(
            "/qps/rest/3.0/search/was/report",
            method="POST",
            body_xml=body,
            accept="xml",
        )

    def download_was_report(self, report_id: int) -> dict[str, Any]:
        """Download a generated report's contents.

        # TODO(verify): this wrapper requests ``accept="xml"`` (the only text
        # format ``self._qps`` can normalize). Reports created with binary formats
        # (PDF, PDF_ENCRYPTED, WORD, POWERPOINT, HTML_ZIPPED) will NOT parse
        # correctly through this path — only XML/CSV-as-text style reports are
        # safe to fetch here. A raw-bytes passthrough mode on
        # ``QualysClient.qps()`` would be needed to support binary report
        # downloads properly; flagged to the orchestrator rather than editing
        # ``client.py`` directly.

        Args:
            report_id: The report ID to download (must be in FINISHED state).

        Returns:
            Parsed report contents for XML-format reports, or a parse/error dict
            for binary formats (see TODO above).
        """
        return self._qps(
            f"/qps/rest/3.0/download/was/report/{report_id}",
            method="GET",
            accept="xml",
        )

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #
    def create_was_report(
        self,
        name: str,
        report_type: str,
        report_format: str = "PDF",
        webapp_id: int | None = None,
        scan_ids: str | None = None,
        template_id: int | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Generate a new WAS report.

        Args:
            name: Report name.
            report_type: "WAS_WEBAPP_REPORT" (per-webapp findings report),
                "WAS_SCAN_REPORT" (single/multi-scan report), or
                "WAS_COMPARISON_REPORT" (diff between two scans).
            report_format: "WORD", "HTML_ZIPPED", "HTML_BASE64", "PDF",
                "PDF_ENCRYPTED", "CSV", "CSV_V2", "XML", or "POWERPOINT".
            webapp_id: Target web application ID. Required for
                "WAS_WEBAPP_REPORT" (max 500 web apps per report per Qualys docs;
                this tool only supports a single ID — pass additional apps via a
                follow-up call or use Qualys tags for bulk reporting).
                # TODO(verify): confirmed body shape is
                # ``config.webAppReport.target.webapps.WebApp.id`` for
                # WAS_WEBAPP_REPORT only.
            scan_ids: Comma-separated scan IDs. Required for "WAS_SCAN_REPORT" and
                "WAS_COMPARISON_REPORT" (comparison expects exactly two).
                # TODO(verify): nested shape — assumed
                # ``config.scanReport.target.scans.WasScan.id`` by analogy with
                # the confirmed webapp-report shape; not directly confirmed.
            template_id: Report template ID to use (optional; Qualys uses the
                account default template if omitted).
            description: Optional free-text description.

        Returns:
            Parsed ``ServiceResponse`` with the new report's ``id`` (poll
            ``search_was_reports``/``get`` for generation status), or an error
            dict.
        """
        if report_type == "WAS_WEBAPP_REPORT":
            target_xml = f"<target><webapps><WebApp><id>{self._esc(webapp_id)}</id></WebApp></webapps></target>"
            config_xml = f"<webAppReport>{target_xml}</webAppReport>"
        else:
            # TODO(verify): WAS_SCAN_REPORT / WAS_COMPARISON_REPORT config shape.
            scan_items = "".join(
                f"<WasScan><id>{self._esc(sid.strip())}</id></WasScan>"
                for sid in (scan_ids or "").split(",")
                if sid.strip()
            )
            target_xml = f"<target><scans>{scan_items}</scans></target>"
            config_xml = f"<scanReport>{target_xml}</scanReport>"

        fields = (
            self._field("name", name)
            + self._field("description", description)
            + self._field("format", report_format)
            + self._field("type", report_type)
            + f"<config>{config_xml}</config>"
            + self._field("template", {"id": template_id} if template_id else None)
        )
        body = self._data_body("Report", fields)
        return self._qps(
            "/qps/rest/3.0/create/was/report",
            method="POST",
            body_xml=body,
            accept="xml",
        )

    # ------------------------------------------------------------------ #
    # Destructive
    # ------------------------------------------------------------------ #
    def delete_was_report(self, report_id: int, confirm: str | None = None) -> dict[str, Any]:
        """Permanently delete a report. IRREVERSIBLE.

        Gated: requires the console to be started with QUALYS_ENABLE_DESTRUCTIVE
        and the caller to pass confirm=<report_id>.

        Args:
            report_id: The report ID to delete.
            confirm: Must equal ``str(report_id)`` to proceed.

        Returns:
            Parsed ``ServiceResponse`` status, or a confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=str(report_id))
        if guard:
            return guard
        return self._qps(
            f"/qps/rest/3.0/delete/was/report/{report_id}",
            method="POST",
            accept="xml",
        )
