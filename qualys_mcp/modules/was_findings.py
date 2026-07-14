"""WAS Findings module (QPS REST 3.0 API).

Web Application Scanning (WAS) is not covered by the classic VM/PC API guide;
it lives entirely under the QPS REST 3.0 family at ``/qps/rest/3.0/.../was/finding``.
Endpoint shapes below are built from the public WAS API reference
(https://docs.qualys.com/en/was/api/finding/) — uncertain nested fields are
flagged with ``# TODO(verify)``.

Docs: Qualys WAS API User Guide — "Findings".
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class WasFindingsModule(BaseModule):
    """Search WAS findings (vulnerabilities/sensitive content/info gathered) and manage their status."""

    module_label = "was_findings"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(server, self.search_was_findings, "search_was_findings", tier="read")
        self._add_tool(server, self.get_was_finding, "get_was_finding", tier="read")
        self._add_tool(server, self.count_was_findings, "count_was_findings", tier="read")
        # Writes
        self._add_tool(server, self.update_was_finding, "update_was_finding", tier="write")

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

    def _finding_filters(
        self,
        finding_id: int | None,
        qid: int | None,
        webapp_id: int | None,
        finding_type: str | None,
        status: str | None,
        severity: int | None,
        ignored_reason: str | None,
        first_detected_after: str | None,
        last_detected_after: str | None,
    ) -> list[str]:
        return [
            self._criteria("id", "EQUALS", finding_id),
            self._criteria("qid", "EQUALS", qid),
            self._criteria("webApp.id", "EQUALS", webapp_id),
            self._criteria("type", "EQUALS", finding_type),
            self._criteria("status", "EQUALS", status),
            self._criteria("severity", "EQUALS", severity),
            self._criteria("ignoredReason", "EQUALS", ignored_reason),
            self._criteria("firstDetectedDate", "GREATER", first_detected_after),
            self._criteria("lastDetectedDate", "GREATER", last_detected_after),
        ]

    # ------------------------------------------------------------------ #
    # Reads
    # ------------------------------------------------------------------ #
    def search_was_findings(
        self,
        finding_id: int | None = None,
        qid: int | None = None,
        webapp_id: int | None = None,
        finding_type: str | None = None,
        status: str | None = None,
        severity: int | None = None,
        ignored_reason: str | None = None,
        first_detected_after: str | None = None,
        last_detected_after: str | None = None,
        limit: int = 20,
        offset: int = 1,
    ) -> dict[str, Any]:
        """Search WAS findings.

        Args:
            finding_id: Restrict to a single finding ID (``id``, EQUALS).
            qid: Restrict to a specific Qualys QID (``qid``, EQUALS).
            webapp_id: Restrict to findings on this web app (``webApp.id``, EQUALS).
            finding_type: "VULNERABILITY", "SENSITIVE_CONTENT", or
                "INFORMATION_GATHERED" (``type``, EQUALS).
            status: "NEW", "ACTIVE", "REOPENED", "PROTECTED", or "FIXED"
                (``status``, EQUALS).
            severity: Severity level 1-5 (``severity``, EQUALS).
            ignored_reason: "FALSE_POSITIVE", "RISK_ACCEPTED", or "NOT_APPLICABLE"
                (``ignoredReason``, EQUALS) — only meaningful for ignored findings.
            first_detected_after: ISO datetime lower bound for ``firstDetectedDate``
                (``YYYY-MM-DDTHH:MM:SSZ``).
            last_detected_after: ISO datetime lower bound for ``lastDetectedDate``.
            limit: Max results per page (preference ``limitResults``).
            offset: 1-based starting offset (preference ``startFromOffset``).

        Returns:
            Parsed ``ServiceResponse`` containing a list of ``Finding`` records.
        """
        criteria = self._finding_filters(
            finding_id,
            qid,
            webapp_id,
            finding_type,
            status,
            severity,
            ignored_reason,
            first_detected_after,
            last_detected_after,
        )
        body = self._search_body(*criteria, limit=limit, offset=offset)
        return self._qps(
            "/qps/rest/3.0/search/was/finding",
            method="POST",
            body_xml=body,
            accept="xml",
        )

    def get_was_finding(self, finding_id: int) -> dict[str, Any]:
        """Fetch full detail for a single finding.

        Args:
            finding_id: The finding ID.

        Returns:
            Parsed ``ServiceResponse`` containing the ``Finding`` record.
        """
        return self._qps(
            f"/qps/rest/3.0/get/was/finding/{finding_id}",
            method="GET",
            accept="xml",
        )

    def count_was_findings(
        self,
        webapp_id: int | None = None,
        finding_type: str | None = None,
        status: str | None = None,
        severity: int | None = None,
    ) -> dict[str, Any]:
        """Count findings matching optional filters.

        Args:
            webapp_id: Restrict to findings on this web app.
            finding_type: "VULNERABILITY", "SENSITIVE_CONTENT", or
                "INFORMATION_GATHERED".
            status: "NEW", "ACTIVE", "REOPENED", "PROTECTED", or "FIXED".
            severity: Severity level 1-5.

        Returns:
            Parsed ``ServiceResponse`` with a ``count`` field.
        """
        criteria = self._finding_filters(
            None, None, webapp_id, finding_type, status, severity, None, None, None
        )
        body = self._search_body(*criteria)
        return self._qps(
            "/qps/rest/3.0/count/was/finding",
            method="POST",
            body_xml=body,
            accept="xml",
        )

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #
    def update_was_finding(
        self,
        finding_id: int,
        is_ignored: bool | None = None,
        ignored_reason: str | None = None,
        ignored_comment: str | None = None,
    ) -> dict[str, Any]:
        """Ignore or reactivate a finding.

        To ignore a finding: pass ``is_ignored=True`` with ``ignored_reason`` (and
        optionally ``ignored_comment``). To reactivate a previously-ignored
        finding: pass ``is_ignored=False``.

        # TODO(verify): the update-finding endpoint path and body shape are not
        # directly confirmed in the public docs excerpt available at build time;
        # this follows the same convention as every other confirmed QPS 3.0
        # resource (webapp/wasscan/webappauthrecord/report all use
        # ``POST /qps/rest/3.0/update/was/<resource>/<id>`` with
        # ``<ServiceRequest><data><Entity>...</Entity></data></ServiceRequest>``).
        # Confirm field names against ``/qps/xsd/3.0/was/finding.xsd`` before
        # relying on this in production.

        Args:
            finding_id: The finding ID to update.
            is_ignored: True to ignore the finding, False to reactivate it.
            ignored_reason: Required when ignoring — one of "FALSE_POSITIVE",
                "RISK_ACCEPTED", "NOT_APPLICABLE", or "OTHER".
            ignored_comment: Free-text comment explaining the ignore/reactivate
                decision.

        Returns:
            Parsed ``ServiceResponse`` with the updated ``Finding`` record, or an
            error dict.
        """
        fields = (
            self._field("isIgnored", is_ignored)
            + self._field("ignoredReason", ignored_reason)
            + self._field("ignoredComment", ignored_comment)
        )
        body = self._data_body("Finding", fields)
        return self._qps(
            f"/qps/rest/3.0/update/was/finding/{finding_id}",
            method="POST",
            body_xml=body,
            accept="xml",
        )
