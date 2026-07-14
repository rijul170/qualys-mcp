"""WAS Web Applications module (QPS REST 3.0 API).

Web Application Scanning (WAS) is not covered by the classic VM/PC API guide;
it lives entirely under the QPS REST 3.0 family at ``/qps/rest/3.0/.../was/webapp``.
Endpoint shapes below are built from the public WAS API reference
(https://docs.qualys.com/en/was/api/web_apps/) — uncertain nested fields are
flagged with ``# TODO(verify)``.

Docs: Qualys WAS API User Guide — "Web Applications".
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class WasWebappsModule(BaseModule):
    """Search, inspect, and manage WAS Web Application assets."""

    module_label = "was_webapps"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(server, self.search_was_webapps, "search_was_webapps", tier="read")
        self._add_tool(server, self.get_was_webapp, "get_was_webapp", tier="read")
        self._add_tool(server, self.count_was_webapps, "count_was_webapps", tier="read")
        # Writes
        self._add_tool(server, self.create_was_webapp, "create_was_webapp", tier="write")
        self._add_tool(server, self.update_was_webapp, "update_was_webapp", tier="write")
        # Destructive
        self._add_tool(server, self.delete_was_webapp, "delete_was_webapp", tier="destructive")

    # ------------------------------------------------------------------ #
    # XML helpers (duplicated per-module by design; modules cannot import
    # shared helpers — see docs/MODULE_BUILD_GUIDE.md section 1).
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

        # TODO(verify): preference element names (``limitResults``/``startFromOffset``)
        # follow the common QPS 3.0 convention but are not confirmed against the WAS
        # API guide excerpt available at build time.
        """
        filters = "".join(c for c in criteria if c)
        prefs_inner = self._field("limitResults", limit) + self._field("startFromOffset", offset)
        prefs = f"<preferences>{prefs_inner}</preferences>" if prefs_inner else ""
        filters_block = f"<filters>{filters}</filters>" if filters else ""
        return f"<ServiceRequest>{prefs}{filters_block}</ServiceRequest>"

    def _data_body(self, entity_tag: str, fields: str) -> str:
        """Build a ``<ServiceRequest><data><Tag>...</Tag></data></ServiceRequest>`` body."""
        return f"<ServiceRequest><data><{entity_tag}>{fields}</{entity_tag}></data></ServiceRequest>"

    def _webapp_filters(
        self,
        webapp_id: int | None,
        name_contains: str | None,
        url_contains: str | None,
        tag_id: int | None,
        tag_name_contains: str | None,
        is_scheduled: bool | None,
        is_scanned: bool | None,
        created_after: str | None,
        updated_after: str | None,
    ) -> list[str]:
        return [
            self._criteria("id", "EQUALS", webapp_id),
            self._criteria("name", "CONTAINS", name_contains),
            self._criteria("url", "CONTAINS", url_contains),
            self._criteria("tags.id", "EQUALS", tag_id),
            self._criteria("tags.name", "CONTAINS", tag_name_contains),
            self._criteria("isScheduled", "EQUALS", is_scheduled),
            self._criteria("isScanned", "EQUALS", is_scanned),
            self._criteria("createdDate", "GREATER", created_after),
            self._criteria("updatedDate", "GREATER", updated_after),
        ]

    # ------------------------------------------------------------------ #
    # Reads
    # ------------------------------------------------------------------ #
    def search_was_webapps(
        self,
        webapp_id: int | None = None,
        name_contains: str | None = None,
        url_contains: str | None = None,
        tag_id: int | None = None,
        tag_name_contains: str | None = None,
        is_scheduled: bool | None = None,
        is_scanned: bool | None = None,
        created_after: str | None = None,
        updated_after: str | None = None,
        limit: int = 20,
        offset: int = 1,
    ) -> dict[str, Any]:
        """Search WAS web application assets.

        Args:
            webapp_id: Restrict to a single web app ID (Criteria field ``id``, EQUALS).
            name_contains: Substring match on the web app name (``name``, CONTAINS).
            url_contains: Substring match on the primary URL (``url``, CONTAINS).
            tag_id: Restrict to web apps carrying this tag ID (``tags.id``, EQUALS).
            tag_name_contains: Substring match on tag name (``tags.name``, CONTAINS).
            is_scheduled: Filter by whether the web app has a scan schedule attached.
            is_scanned: Filter by whether the web app has ever been scanned.
            created_after: ISO datetime lower bound for ``createdDate``
                (``YYYY-MM-DDTHH:MM:SSZ``).
            updated_after: ISO datetime lower bound for ``updatedDate``.
            limit: Max results per page (maps to preference ``limitResults``).
            offset: 1-based starting offset (maps to preference ``startFromOffset``).

        Returns:
            Parsed ``ServiceResponse`` containing a list of ``WebApp`` records.
        """
        criteria = self._webapp_filters(
            webapp_id,
            name_contains,
            url_contains,
            tag_id,
            tag_name_contains,
            is_scheduled,
            is_scanned,
            created_after,
            updated_after,
        )
        body = self._search_body(*criteria, limit=limit, offset=offset)
        return self._qps(
            "/qps/rest/3.0/search/was/webapp",
            method="POST",
            body_xml=body,
            accept="xml",
        )

    def get_was_webapp(self, webapp_id: int) -> dict[str, Any]:
        """Fetch full detail for a single web application.

        Args:
            webapp_id: The web application ID.

        Returns:
            Parsed ``ServiceResponse`` containing the ``WebApp`` record.
        """
        return self._qps(
            f"/qps/rest/3.0/get/was/webapp/{webapp_id}",
            method="GET",
            accept="xml",
        )

    def count_was_webapps(
        self,
        name_contains: str | None = None,
        url_contains: str | None = None,
        tag_id: int | None = None,
        tag_name_contains: str | None = None,
        is_scheduled: bool | None = None,
        is_scanned: bool | None = None,
    ) -> dict[str, Any]:
        """Count web applications matching optional filters.

        Args:
            name_contains: Substring match on web app name.
            url_contains: Substring match on primary URL.
            tag_id: Restrict to web apps carrying this tag ID.
            tag_name_contains: Substring match on tag name.
            is_scheduled: Filter by whether a scan schedule is attached.
            is_scanned: Filter by whether the web app has ever been scanned.

        Returns:
            Parsed ``ServiceResponse`` with a ``count`` field.
        """
        criteria = self._webapp_filters(
            None,
            name_contains,
            url_contains,
            tag_id,
            tag_name_contains,
            is_scheduled,
            is_scanned,
            None,
            None,
        )
        body = self._search_body(*criteria)
        return self._qps(
            "/qps/rest/3.0/count/was/webapp",
            method="POST",
            body_xml=body,
            accept="xml",
        )

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #
    def create_was_webapp(
        self,
        name: str,
        url: str,
        tag_ids: str | None = None,
        auth_record_id: int | None = None,
        additional_uris: str | None = None,
        scanner_appliance_type: str | None = None,
        comments: str | None = None,
    ) -> dict[str, Any]:
        """Create a new WAS web application asset.

        Args:
            name: Display name for the web application.
            url: Primary URL to scan (e.g. "https://www.example.com").
            tag_ids: Comma-separated tag IDs to attach at creation.
                # TODO(verify): exact nested XML — likely
                # ``<tags><set><TagList><Tag><id>..</id></Tag>...</TagList></set></tags>``.
            auth_record_id: Existing WebAppAuthRecord ID to attach as the default
                authentication record.
                # TODO(verify): field name/nesting for attaching an auth record at
                # create time (``authRecord`` vs ``authRecords.add``).
            additional_uris: Comma-separated additional URIs to include in scope.
                # TODO(verify): element name (``uris``) and list wrapper shape.
            scanner_appliance_type: "EXTERNAL" or "INTERNAL" scanner appliance type.
                # TODO(verify): nested shape (``scannerAppliance.type`` vs a scanner
                # tag reference) — Qualys WAS supports both external and internal
                # (via a scanner appliance tag) scanning.
            comments: Free-text comment/description for the web app.

        Returns:
            Parsed ``ServiceResponse`` with the created ``WebApp`` (including new ``id``).
        """
        fields = (
            self._field("name", name)
            + self._field("url", url)
            + self._field("tags", {"id": tag_ids} if tag_ids else None)  # TODO(verify)
            + self._field("authRecord", {"id": auth_record_id} if auth_record_id else None)  # TODO(verify)
            + self._field("uris", additional_uris)  # TODO(verify)
            + self._field("scannerAppliance", {"type": scanner_appliance_type} if scanner_appliance_type else None)  # TODO(verify)
            + self._field("comments", comments)
        )
        body = self._data_body("WebApp", fields)
        return self._qps(
            "/qps/rest/3.0/create/was/webapp",
            method="POST",
            body_xml=body,
            accept="xml",
        )

    def update_was_webapp(
        self,
        webapp_id: int,
        name: str | None = None,
        url: str | None = None,
        comments: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing web application's basic fields.

        Args:
            webapp_id: The web application ID to update.
            name: New display name, if changing.
            url: New primary URL, if changing.
            comments: New free-text comment, if changing.

        Returns:
            Parsed ``ServiceResponse`` with the updated ``WebApp`` record.
        """
        fields = (
            self._field("name", name) + self._field("url", url) + self._field("comments", comments)
        )
        body = self._data_body("WebApp", fields)
        return self._qps(
            f"/qps/rest/3.0/update/was/webapp/{webapp_id}",
            method="POST",
            body_xml=body,
            accept="xml",
        )

    # ------------------------------------------------------------------ #
    # Destructive
    # ------------------------------------------------------------------ #
    def delete_was_webapp(
        self,
        webapp_id: int,
        remove_from_subscription: bool = False,
        confirm: str | None = None,
    ) -> dict[str, Any]:
        """Permanently delete a web application. IRREVERSIBLE.

        Gated: requires the console to be started with QUALYS_ENABLE_DESTRUCTIVE
        and the caller to pass confirm=<webapp_id>.

        Args:
            webapp_id: The web application ID to delete.
            remove_from_subscription: When True, also remove the underlying asset
                from the subscription (adds ``?action=removeFromSubscription``).
                Per Qualys docs, deleting a web app does NOT remove the asset unless
                this flag is set.
            confirm: Must equal ``str(webapp_id)`` to proceed.

        Returns:
            Parsed ``ServiceResponse`` status, or a confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=str(webapp_id))
        if guard:
            return guard
        params = {"action": "removeFromSubscription"} if remove_from_subscription else None
        return self._qps(
            f"/qps/rest/3.0/delete/was/webapp/{webapp_id}",
            method="POST",
            params=params,
            accept="xml",
        )
