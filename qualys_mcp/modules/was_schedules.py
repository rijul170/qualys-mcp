"""WAS Scan Schedules module (QPS REST 3.0 API).

Web Application Scanning (WAS) is not covered by the classic VM/PC API guide;
it lives entirely under the QPS REST 3.0 family, believed to be at
``/qps/rest/3.0/.../was/wasscanschedule`` (the ``WasScanSchedule`` resource).
This is the least-documented corner of the WAS API surface reachable without
an authenticated session — every nested body field below is a best-effort
inference from the WAS API guide's schedule feature list and is flagged
``# TODO(verify)``. Confirm against the live WAS API guide / XSD
(``/qps/xsd/3.0/was/wasscanschedule.xsd``) before relying on writes here.

Docs: Qualys WAS API User Guide — "Schedules" (search/get/create/update/
activate/deactivate/delete/download-to-iCal operations on ``WasScanSchedule``).
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class WasSchedulesModule(BaseModule):
    """Search, inspect, and manage WAS recurring scan schedules."""

    module_label = "was_schedules"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(server, self.search_was_schedules, "search_was_schedules", tier="read")
        self._add_tool(server, self.get_was_schedule, "get_was_schedule", tier="read")
        # Writes
        self._add_tool(server, self.create_was_schedule, "create_was_schedule", tier="write")
        self._add_tool(server, self.update_was_schedule, "update_was_schedule", tier="write")
        # Destructive
        self._add_tool(server, self.delete_was_schedule, "delete_was_schedule", tier="destructive")

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
    def search_was_schedules(
        self,
        schedule_id: int | None = None,
        name_contains: str | None = None,
        webapp_id: int | None = None,
        active: bool | None = None,
        limit: int = 20,
        offset: int = 1,
    ) -> dict[str, Any]:
        """Search recurring WAS scan schedules.

        # TODO(verify): resource path (``was/wasscanschedule``) and Criteria field
        # names below are inferred by analogy with the confirmed ``wasscan``
        # search filters (``id``, ``name``, ``webApp.id``); not directly confirmed
        # for the schedule resource.

        Args:
            schedule_id: Restrict to a single schedule ID (``id``, EQUALS).
            name_contains: Substring match on schedule name (``name``, CONTAINS).
            webapp_id: Restrict to schedules targeting this web app
                (``webApp.id``, EQUALS).
            active: Filter by whether the schedule is currently active
                (``active``, EQUALS).
            limit: Max results per page (preference ``limitResults``).
            offset: 1-based starting offset (preference ``startFromOffset``).

        Returns:
            Parsed ``ServiceResponse`` containing a list of ``WasScanSchedule``
            records.
        """
        criteria = [
            self._criteria("id", "EQUALS", schedule_id),
            self._criteria("name", "CONTAINS", name_contains),
            self._criteria("webApp.id", "EQUALS", webapp_id),
            self._criteria("active", "EQUALS", active),
        ]
        body = self._search_body(*criteria, limit=limit, offset=offset)
        return self._qps(
            "/qps/rest/3.0/search/was/wasscanschedule",  # TODO(verify): resource path
            method="POST",
            body_xml=body,
            accept="xml",
        )

    def get_was_schedule(self, schedule_id: int) -> dict[str, Any]:
        """Fetch full detail for a single scan schedule.

        # TODO(verify): resource path (``was/wasscanschedule``) not directly
        # confirmed for the GET-by-id form.

        Args:
            schedule_id: The schedule ID.

        Returns:
            Parsed ``ServiceResponse`` containing the ``WasScanSchedule`` record.
        """
        return self._qps(
            f"/qps/rest/3.0/get/was/wasscanschedule/{schedule_id}",  # TODO(verify)
            method="GET",
            accept="xml",
        )

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #
    def create_was_schedule(
        self,
        name: str,
        webapp_id: int,
        scan_type: str = "VULNERABILITY",
        profile_id: int | None = None,
        start_date: str | None = None,
        occurrence_type: str | None = None,
        active: bool = True,
    ) -> dict[str, Any]:
        """Create a recurring scan schedule for a web application.

        # TODO(verify): This entire body shape is a best-effort inference and
        # NOT confirmed against a real create-schedule XML example. Qualys WAS
        # schedules are known to wrap a ``WasScan``-shaped launch definition plus
        # frequency/recurrence fields (start date/time, timezone, occurrence
        # type such as DAILY/WEEKLY/MONTHLY, interval, day-of-week/month) — the
        # exact element names (e.g. ``Frequency``, ``timeZone``,
        # ``occurrenceType``) must be confirmed against the WAS API guide or
        # ``/qps/xsd/3.0/was/wasscanschedule.xsd`` before this is used in
        # production. Treat this method as a starting scaffold, not a verified
        # implementation.

        Args:
            name: Display name for the schedule.
            webapp_id: Target web application ID for the scheduled scan.
            scan_type: "VULNERABILITY" or "DISCOVERY".
            profile_id: Option profile ID to use for each scheduled run.
            start_date: ISO datetime for the first run
                (``YYYY-MM-DDTHH:MM:SSZ``).
            occurrence_type: Recurrence pattern — e.g. "DAILY", "WEEKLY",
                "MONTHLY" (exact enum unconfirmed).
            active: Whether the schedule is active on creation.

        Returns:
            Parsed ``ServiceResponse`` with the created ``WasScanSchedule``
            (including new ``id``), or an error dict.
        """
        scan_fields = (
            self._field("type", scan_type)
            + f"<target><webApp>{self._field('id', webapp_id)}</webApp></target>"
            + self._field("profile", {"id": profile_id} if profile_id else None)
        )
        fields = (
            self._field("name", name)
            + self._field("active", active)
            + f"<wasScan>{scan_fields}</wasScan>"  # TODO(verify): wrapper element name
            + self._field("startDate", start_date)  # TODO(verify): field name
            + self._field("occurrenceType", occurrence_type)  # TODO(verify): field name
        )
        body = self._data_body("WasScanSchedule", fields)
        return self._qps(
            "/qps/rest/3.0/create/was/wasscanschedule",  # TODO(verify): resource path
            method="POST",
            body_xml=body,
            accept="xml",
        )

    def update_was_schedule(
        self,
        schedule_id: int,
        name: str | None = None,
        active: bool | None = None,
        start_date: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing scan schedule (also used to activate/deactivate it).

        # TODO(verify): resource path and field names — see create_was_schedule
        # for the same caveats. Setting ``active`` here is assumed to be
        # equivalent to Qualys's dedicated activate/deactivate schedule actions,
        # but that is not confirmed; a separate ``activate``/``deactivate``
        # action endpoint may be required instead of a plain field update.

        Args:
            schedule_id: The schedule ID to update.
            name: New display name, if changing.
            active: Set True to activate, False to deactivate the schedule.
            start_date: New first-run ISO datetime, if changing.

        Returns:
            Parsed ``ServiceResponse`` with the updated ``WasScanSchedule``
            record.
        """
        fields = (
            self._field("name", name) + self._field("active", active) + self._field("startDate", start_date)
        )
        body = self._data_body("WasScanSchedule", fields)
        return self._qps(
            f"/qps/rest/3.0/update/was/wasscanschedule/{schedule_id}",  # TODO(verify)
            method="POST",
            body_xml=body,
            accept="xml",
        )

    # ------------------------------------------------------------------ #
    # Destructive
    # ------------------------------------------------------------------ #
    def delete_was_schedule(self, schedule_id: int, confirm: str | None = None) -> dict[str, Any]:
        """Permanently delete a scan schedule. IRREVERSIBLE.

        Gated: requires the console to be started with QUALYS_ENABLE_DESTRUCTIVE
        and the caller to pass confirm=<schedule_id>.

        # TODO(verify): resource path not directly confirmed for the delete
        # form of the schedule resource.

        Args:
            schedule_id: The schedule ID to delete.
            confirm: Must equal ``str(schedule_id)`` to proceed.

        Returns:
            Parsed ``ServiceResponse`` status, or a confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=str(schedule_id))
        if guard:
            return guard
        return self._qps(
            f"/qps/rest/3.0/delete/was/wasscanschedule/{schedule_id}",  # TODO(verify)
            method="POST",
            accept="xml",
        )
