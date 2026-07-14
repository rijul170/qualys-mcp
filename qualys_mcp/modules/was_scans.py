"""WAS Scans module (QPS REST 3.0 API).

Web Application Scanning (WAS) is not covered by the classic VM/PC API guide;
it lives entirely under the QPS REST 3.0 family at ``/qps/rest/3.0/.../was/wasscan``.
Endpoint shapes below are built from the public WAS API reference
(https://docs.qualys.com/en/was/api/scans/) — uncertain nested fields are
flagged with ``# TODO(verify)``.

Docs: Qualys WAS API User Guide — "Scans".
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class WasScansModule(BaseModule):
    """Search, launch, monitor, and manage WAS scans."""

    module_label = "was_scans"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(server, self.search_was_scans, "search_was_scans", tier="read")
        self._add_tool(server, self.get_was_scan, "get_was_scan", tier="read")
        self._add_tool(server, self.get_was_scan_status, "get_was_scan_status", tier="read")
        # Writes
        self._add_tool(server, self.launch_was_scan, "launch_was_scan", tier="write")
        self._add_tool(server, self.cancel_was_scan, "cancel_was_scan", tier="write")
        # Destructive
        self._add_tool(server, self.delete_was_scan, "delete_was_scan", tier="destructive")

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
    def search_was_scans(
        self,
        scan_id: int | None = None,
        name_contains: str | None = None,
        webapp_id: int | None = None,
        webapp_name_contains: str | None = None,
        scan_type: str | None = None,
        mode: str | None = None,
        status: str | None = None,
        launched_after: str | None = None,
        launched_before: str | None = None,
        limit: int = 20,
        offset: int = 1,
    ) -> dict[str, Any]:
        """Search WAS scans.

        Args:
            scan_id: Restrict to a single scan ID (Criteria field ``id``, EQUALS).
            name_contains: Substring match on scan name (``name``, CONTAINS).
            webapp_id: Restrict to scans of this web app (``webApp.id``, EQUALS).
            webapp_name_contains: Substring match on web app name (``webApp.name``,
                CONTAINS).
            scan_type: "VULNERABILITY" or "DISCOVERY" (``type``, EQUALS).
            mode: "ONDEMAND", "SCHEDULED", or "API" (``mode``, EQUALS).
            status: "SUBMITTED", "RUNNING", "FINISHED", "ERROR", "CANCELED", or
                "PROCESSING" (``status``, EQUALS).
            launched_after: ISO datetime lower bound for ``launchedDate``
                (``YYYY-MM-DDTHH:MM:SSZ``).
            launched_before: ISO datetime upper bound for ``launchedDate``.
            limit: Max results per page (preference ``limitResults``).
            offset: 1-based starting offset (preference ``startFromOffset``).

        Returns:
            Parsed ``ServiceResponse`` containing a list of ``WasScan`` records.
        """
        criteria = [
            self._criteria("id", "EQUALS", scan_id),
            self._criteria("name", "CONTAINS", name_contains),
            self._criteria("webApp.id", "EQUALS", webapp_id),
            self._criteria("webApp.name", "CONTAINS", webapp_name_contains),
            self._criteria("type", "EQUALS", scan_type),
            self._criteria("mode", "EQUALS", mode),
            self._criteria("status", "EQUALS", status),
            self._criteria("launchedDate", "GREATER", launched_after),
            self._criteria("launchedDate", "LESSER", launched_before),  # TODO(verify): operator name
        ]
        body = self._search_body(*criteria, limit=limit, offset=offset)
        return self._qps(
            "/qps/rest/3.0/search/was/wasscan",
            method="POST",
            body_xml=body,
            accept="xml",
        )

    def get_was_scan(self, scan_id: int) -> dict[str, Any]:
        """Fetch full detail for a single scan (includes status, target, profile).

        Args:
            scan_id: The scan ID.

        Returns:
            Parsed ``ServiceResponse`` containing the ``WasScan`` record.
        """
        return self._qps(
            f"/qps/rest/3.0/get/was/wasscan/{scan_id}",
            method="GET",
            accept="xml",
        )

    def get_was_scan_status(self, scan_id: int) -> dict[str, Any]:
        """Fetch the current status of a scan.

        # TODO(verify): the WAS API v3 has no separate lightweight "status" endpoint
        # distinct from Get Scan Details (unlike the classic VM API's scan/fetch
        # action codes). This calls the same Get Scan Details endpoint and the
        # caller should read the ``status`` field (SUBMITTED/RUNNING/FINISHED/
        # ERROR/CANCELED/PROCESSING) from the response.

        Args:
            scan_id: The scan ID.

        Returns:
            Parsed ``ServiceResponse`` containing the ``WasScan`` record, whose
            ``status`` field reflects the current scan state.
        """
        return self._qps(
            f"/qps/rest/3.0/get/was/wasscan/{scan_id}",
            method="GET",
            accept="xml",
        )

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #
    def launch_was_scan(
        self,
        name: str,
        webapp_id: int,
        scan_type: str = "VULNERABILITY",
        profile_id: int | None = None,
        auth_record_id: int | None = None,
        use_default_auth_record: bool | None = None,
        cancel_after_n_hours: int | None = None,
        send_mail: bool | None = None,
        send_one_mail: bool | None = None,
    ) -> dict[str, Any]:
        """Launch a new WAS scan against a web application.

        Args:
            name: Title for the scan.
            webapp_id: Target web application ID (``target.webApp.id``).
            scan_type: "VULNERABILITY" or "DISCOVERY".
            profile_id: Option profile ID to use (``profile.id``). If omitted,
                the web app's default profile is used.
            auth_record_id: Specific WebAppAuthRecord ID to use for this scan
                (``target.webAppAuthRecord.id``). Mutually exclusive with
                ``use_default_auth_record``.
            use_default_auth_record: Use the web app's default auth record
                (``target.webAppAuthRecord.isDefault`` = true). Mutually exclusive
                with ``auth_record_id``.
            cancel_after_n_hours: Auto-cancel the scan after this many hours.
            send_mail: Send a completion notification email.
            send_one_mail: Send one consolidated email (for multi-webapp scans).

        Returns:
            Parsed ``ServiceResponse`` with the new scan's ``id``/``reference``,
            or an error dict.
        """
        target_auth = None
        if auth_record_id is not None:
            target_auth = {"id": auth_record_id}
        elif use_default_auth_record:
            target_auth = {"isDefault": True}

        target_fields = self._field("webApp", {"id": webapp_id}) + self._field(
            "webAppAuthRecord", target_auth
        )
        fields = (
            self._field("name", name)
            + self._field("type", scan_type)
            + f"<target>{target_fields}</target>"
            + self._field("profile", {"id": profile_id} if profile_id else None)
            + self._field("cancelAfterNHours", cancel_after_n_hours)
            + self._field("sendMail", send_mail)
            + self._field("sendOneMail", send_one_mail)
        )
        body = self._data_body("WasScan", fields)
        return self._qps(
            "/qps/rest/3.0/launch/was/wasscan/",
            method="POST",
            body_xml=body,
            accept="xml",
        )

    def cancel_was_scan(self, scan_id: int, cancel_with_results: bool | None = None) -> dict[str, Any]:
        """Cancel a running scan (reversible in the sense that it does not delete data).

        Args:
            scan_id: The scan ID to cancel.
            cancel_with_results: When True, retain partial results collected so far
                (``cancelWithResults``). Qualys recommends only using this after the
                scan has been RUNNING for at least ~20 minutes, and it applies only
                to single/child scans (not parent multi-webapp scans).
                # TODO(verify): exact request body wrapper — assumed
                # ``<data><WasScan><cancelWithResults>..</cancelWithResults></WasScan></data>``.

        Returns:
            Parsed ``ServiceResponse`` status, or an error dict.
        """
        if cancel_with_results is None:
            body = "<ServiceRequest/>"
        else:
            fields = self._field("cancelWithResults", cancel_with_results)
            body = self._data_body("WasScan", fields)
        return self._qps(
            f"/qps/rest/3.0/cancel/was/wasscan/{scan_id}",
            method="POST",
            body_xml=body,
            accept="xml",
        )

    # ------------------------------------------------------------------ #
    # Destructive
    # ------------------------------------------------------------------ #
    def delete_was_scan(self, scan_id: int, confirm: str | None = None) -> dict[str, Any]:
        """Permanently delete a scan and its results. IRREVERSIBLE.

        Gated: requires the console to be started with QUALYS_ENABLE_DESTRUCTIVE
        and the caller to pass confirm=<scan_id>.

        Args:
            scan_id: The scan ID to delete.
            confirm: Must equal ``str(scan_id)`` to proceed.

        Returns:
            Parsed ``ServiceResponse`` status, or a confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=str(scan_id))
        if guard:
            return guard
        return self._qps(
            f"/qps/rest/3.0/delete/was/wasscan/{scan_id}",
            method="POST",
            accept="xml",
        )
