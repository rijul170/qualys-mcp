"""WAS Web Application Authentication Records module (QPS REST 3.0 API).

Web Application Scanning (WAS) is not covered by the classic VM/PC API guide;
it lives entirely under the QPS REST 3.0 family at
``/qps/rest/3.0/.../was/webappauthrecord``. Endpoint shapes below are built
from the public WAS API reference (https://docs.qualys.com/en/was/api/auth/) —
uncertain nested fields are flagged with ``# TODO(verify)``.

Docs: Qualys WAS API User Guide — "Authentication Records".
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class WasAuthModule(BaseModule):
    """Search, inspect, and manage WAS web application authentication records."""

    module_label = "was_auth"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(server, self.search_was_auth_records, "search_was_auth_records", tier="read")
        self._add_tool(server, self.get_was_auth_record, "get_was_auth_record", tier="read")
        # Writes
        self._add_tool(server, self.create_was_auth_record, "create_was_auth_record", tier="write")
        self._add_tool(server, self.update_was_auth_record, "update_was_auth_record", tier="write")
        # Destructive
        self._add_tool(server, self.delete_was_auth_record, "delete_was_auth_record", tier="destructive")

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
    def search_was_auth_records(
        self,
        auth_record_id: int | None = None,
        name_contains: str | None = None,
        tag_id: int | None = None,
        is_used: bool | None = None,
        limit: int = 20,
        offset: int = 1,
    ) -> dict[str, Any]:
        """Search web application authentication records.

        Args:
            auth_record_id: Restrict to a single auth record ID (``id``, EQUALS).
            name_contains: Substring match on record name (``name``, CONTAINS).
            tag_id: Restrict to records carrying this tag ID (``tags.id``, EQUALS).
            is_used: Filter by whether the record is attached to any web app
                (``isUsed``, EQUALS).
            limit: Max results per page (preference ``limitResults``).
            offset: 1-based starting offset (preference ``startFromOffset``).

        Returns:
            Parsed ``ServiceResponse`` containing a list of ``WebAppAuthRecord``
            records.
        """
        criteria = [
            self._criteria("id", "EQUALS", auth_record_id),
            self._criteria("name", "CONTAINS", name_contains),
            self._criteria("tags.id", "EQUALS", tag_id),
            self._criteria("isUsed", "EQUALS", is_used),
        ]
        body = self._search_body(*criteria, limit=limit, offset=offset)
        return self._qps(
            "/qps/rest/3.0/search/was/webappauthrecord",
            method="POST",
            body_xml=body,
            accept="xml",
        )

    def get_was_auth_record(self, auth_record_id: int) -> dict[str, Any]:
        """Fetch full detail for a single authentication record.

        Args:
            auth_record_id: The authentication record ID.

        Returns:
            Parsed ``ServiceResponse`` containing the ``WebAppAuthRecord`` record.
        """
        return self._qps(
            f"/qps/rest/3.0/get/was/webappauthrecord/{auth_record_id}",
            method="GET",
            accept="xml",
        )

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #
    def create_was_auth_record(
        self,
        name: str,
        record_type: str = "FORM_STANDARD",
        username: str | None = None,
        password: str | None = None,
        selenium_script: str | None = None,
        comments: str | None = None,
    ) -> dict[str, Any]:
        """Create a new web application authentication record.

        Args:
            name: Display name for the auth record.
            record_type: One of "FORM_STANDARD" (standard login form),
                "FORM_CUSTOM" (custom form fields), "FORM_SELENIUM" (Selenium
                script based login), "SERVER_BASIC", "SERVER_DIGEST",
                "SERVER_NTLM", or "CERTIFICATE".
                # TODO(verify): confirm this is the literal value of the
                # ``formRecord.type`` (or ``serverRecord.type``) sub-element
                # rather than a top-level discriminator — nesting differs between
                # form-based and server-based records per the WAS auth reference.
            username: Login username. Required for FORM_STANDARD/SERVER_* types.
            password: Login password. Required for FORM_STANDARD/SERVER_* types.
            selenium_script: Raw Selenium IDE script content. Required for
                FORM_SELENIUM; embed ``@@authusername@@``/``@@authpassword@@``
                placeholders and set ``seleniumCreds`` to true if credentials
                should be substituted at scan time.
                # TODO(verify): exact element name/wrapper for the Selenium script
                # payload and the ``seleniumCreds`` flag placement.
            comments: Free-text comment/description.

        Returns:
            Parsed ``ServiceResponse`` with the created ``WebAppAuthRecord``
            (including new ``id``).
        """
        # TODO(verify): the form-record sub-object nesting below (formRecord/type/
        # username/password) is inferred from the WAS auth reference field list
        # and is not confirmed against a full create-request example.
        form_fields = (
            self._field("type", record_type)
            + self._field("username", username)
            + self._field("password", password)
            + self._field("seleniumScript", selenium_script)
        )
        fields = (
            self._field("name", name)
            + f"<formRecord>{form_fields}</formRecord>"
            + self._field("comments", comments)
        )
        body = self._data_body("WebAppAuthRecord", fields)
        return self._qps(
            "/qps/rest/3.0/create/was/webappauthrecord/",
            method="POST",
            body_xml=body,
            accept="xml",
        )

    def update_was_auth_record(
        self,
        auth_record_id: int,
        name: str | None = None,
        username: str | None = None,
        password: str | None = None,
        comments: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing authentication record's fields.

        Args:
            auth_record_id: The authentication record ID to update.
            name: New display name, if changing.
            username: New login username, if changing.
                # TODO(verify): confirm ``username``/``password`` live directly
                # under ``formRecord`` on update the same way as create.
            password: New login password, if changing.
            comments: New free-text comment, if changing.

        Returns:
            Parsed ``ServiceResponse`` with the updated ``WebAppAuthRecord``
            record.
        """
        form_fields = self._field("username", username) + self._field("password", password)
        fields = (
            self._field("name", name)
            + (f"<formRecord>{form_fields}</formRecord>" if form_fields else "")
            + self._field("comments", comments)
        )
        body = self._data_body("WebAppAuthRecord", fields)
        return self._qps(
            f"/qps/rest/3.0/update/was/webappauthrecord/{auth_record_id}",
            method="POST",
            body_xml=body,
            accept="xml",
        )

    # ------------------------------------------------------------------ #
    # Destructive
    # ------------------------------------------------------------------ #
    def delete_was_auth_record(self, auth_record_id: int, confirm: str | None = None) -> dict[str, Any]:
        """Permanently delete an authentication record. IRREVERSIBLE.

        Gated: requires the console to be started with QUALYS_ENABLE_DESTRUCTIVE
        and the caller to pass confirm=<auth_record_id>. Note: Qualys will reject
        deletion of auth records still attached to a web app (``isUsed=true``).

        Args:
            auth_record_id: The authentication record ID to delete.
            confirm: Must equal ``str(auth_record_id)`` to proceed.

        Returns:
            Parsed ``ServiceResponse`` status, or a confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=str(auth_record_id))
        if guard:
            return guard
        return self._qps(
            f"/qps/rest/3.0/delete/was/webappauthrecord/{auth_record_id}",
            method="POST",
            accept="xml",
        )
